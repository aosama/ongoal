/**
 * OnGoal Frontend - Vue.js 3 application with WebSocket + REST integration
 *
 * Features:
 * - Real-time chat with LLM streaming responses
 * - Goal sidebar with Goals/Timeline/Events tabs
 * - Goal cards with type badges, lock/complete controls, evaluation status
 * - Goal glyph click to expand evaluation details
 * - Pipeline controls (toggle infer/merge/evaluate stages)
 * - LLM status badge with provider, model, and cost info
 */
const { createApp, ref, reactive, computed, onMounted, nextTick, watch } = Vue;

// Configuration
const API_BASE = window.__API_BASE__ || `http://${window.location.hostname}:8000`;
const WS_URL = window.__WS_URL__ || `ws://${window.location.hostname}:8000/ws`;
const CONVERSATION_ID = 'default';

/* Goal type config — colors and icons */
const GOAL_TYPES = {
    question:  { color: 'blue',  bg: 'bg-blue-100', text: 'text-blue-800', ring: 'ring-blue-400', icon: '?' },
    request:   { color: 'green', bg: 'bg-emerald-100', text: 'text-emerald-800', ring: 'ring-emerald-400', icon: '!' },
    offer:     { color: 'amber', bg: 'bg-amber-100', text: 'text-amber-800', ring: 'ring-amber-400', icon: '🎁' },
    suggestion:{ color: 'red',  bg: 'bg-red-100', text: 'text-red-800', ring: 'ring-red-400', icon: '💡' },
};

const EVAL_STYLES = {
    confirm:    { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-300', icon: '✓' },
    contradict: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300', icon: '✗' },
    ignore:     { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-300', icon: '⊘' },
};

createApp({
    setup() {
        // --- State ---
        const messages = ref([]);
        const goals = ref([]);
        const currentMessage = ref('');
        const isStreaming = ref(false);
        const activeTab = ref('Goals');
        const ws = ref(null);
        const messagesContainer = ref(null);
        const timelineData = ref([]);
        const llmStatus = ref(null);
        const selectedGoalId = ref(null);
        const keyphrases = ref({});
        const alerts = ref([]);

        const pipelineSettings = reactive({
            infer: true,
            merge: true,
            evaluate: true
        });

        const streamingMessage = ref({
            id: '', content: '', role: 'assistant', timestamp: ''
        });

        // --- Computed ---
        const selectedGoal = computed(() => {
            if (!selectedGoalId.value) return null;
            return goals.value.find(g => g.id === selectedGoalId.value) || null;
        });

        const allKeyphrases = computed(() => {
            const all = [];
            Object.values(keyphrases.value).forEach(phrases => {
                all.push(...phrases);
            });
            return [...new Set(all)]; // deduplicate
        });

        const goalTypeConfig = (type) => GOAL_TYPES[type] || GOAL_TYPES.suggestion;
        const evalStyleFor = (status) => EVAL_STYLES[status] || EVAL_STYLES.ignore;

        // --- API Helpers ---
        const apiCall = async (path, options = {}) => {
            try {
                const res = await fetch(`${API_BASE}${path}`, {
                    headers: { 'Content-Type': 'application/json' },
                    ...options
                });
                if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
                return await res.json();
            } catch (err) {
                console.error('API call failed:', path, err);
                return null;
            }
        };

        // --- LLM Status ---
        const fetchLlmStatus = async () => {
            const data = await apiCall('/api/llm-status');
            if (data) llmStatus.value = data;
        };

        // --- Goal Selection ---
        const selectGoal = (goalId) => {
            selectedGoalId.value = selectedGoalId.value === goalId ? null : goalId;
        };

        const dismissAlert = (index) => {
            alerts.value.splice(index, 1);
        };

        const alertIcon = (type) => {
            switch (type) {
                case 'forgetting': return '🧠';
                case 'contradiction': return '⚡';
                case 'derailment': return '🚂';
                default: return '⚠️';
            }
        };

        const alertSeverityClass = (severity) => {
            switch (severity) {
                case 'critical': return 'bg-red-50 border-red-300 text-red-800';
                case 'warning': return 'bg-amber-50 border-amber-300 text-amber-800';
                default: return 'bg-blue-50 border-blue-300 text-blue-800';
            }
        };

        // --- Keyphrases ---
        const fetchKeyphrases = async () => {
            const data = await apiCall(`/api/conversations/${CONVERSATION_ID}/keyphrases`);
            if (data && data.keyphrases) {
                keyphrases.value[data.message_id || 'latest'] = data.keyphrases;
            }
        };

        // --- WebSocket ---
        const connectWebSocket = () => {
            try {
                ws.value = new WebSocket(WS_URL);

                ws.value.onopen = () => {
                    sendWs({ type: 'get_conversation' });
                };

                ws.value.onmessage = (event) => {
                    handleWsMessage(JSON.parse(event.data));
                };

                ws.value.onclose = () => {
                    setTimeout(connectWebSocket, 3000);
                };

                ws.value.onerror = () => {
                    // onclose will handle reconnection
                };
            } catch (err) {
                console.error('WebSocket connect failed:', err);
                setTimeout(connectWebSocket, 3000);
            }
        };

        const sendWs = (data) => {
            if (ws.value?.readyState === WebSocket.OPEN) {
                ws.value.send(JSON.stringify(data));
            }
        };

        // --- WebSocket Message Handler ---
        const handleWsMessage = (data) => {
            switch (data.type) {
                case 'conversation_state':
                    messages.value = data.conversation.messages;
                    goals.value = data.conversation.goals;
                    alerts.value = data.conversation.alerts || [];
                    if (data.conversation.pipeline_settings) {
                        const ps = data.conversation.pipeline_settings;
                        pipelineSettings.infer = ps.infer ?? ps.infer ?? true;
                        pipelineSettings.merge = ps.merge ?? true;
                        pipelineSettings.evaluate = ps.evaluate ?? true;
                    }
                    break;

                case 'goals_inferred': {
                    const last = messages.value[messages.value.length - 1];
                    if (last?.role === 'user') last.goals = data.goals;
                    goals.value.push(...data.goals);
                    updateTimelineInference(data.goals);
                    break;
                }

                case 'goals_updated':
                    goals.value = [...data.goals];
                    // Update per-message goal mappings
                    messages.value.forEach(msg => {
                        if (msg.role === 'user') {
                            const msgGoals = data.goals.filter(g => g.source_message_id === msg.id);
                            if (msgGoals.length > 0) msg.goals = msgGoals;
                        }
                    });
                    updateTimelineMerge(data);
                    break;

                case 'goals_evaluated':
                    data.evaluations.forEach(ev => {
                        const goal = goals.value.find(g => g.id === ev.goal_id);
                        if (goal) {
                            goal.status = ev.category;
                            goal.evaluation = ev;
                        }
                    });
                    updateTimelineEvaluation(data.evaluations);
                    break;

                case 'llm_response_chunk':
                    if (streamingMessage.value.id !== data.message_id) {
                        streamingMessage.value = {
                            id: data.message_id,
                            content: data.text,
                            role: 'assistant',
                            timestamp: new Date().toISOString()
                        };
                    } else {
                        streamingMessage.value.content += data.text;
                    }
                    const lastMsg = messages.value[messages.value.length - 1];
                    if (lastMsg?.role === 'assistant' && lastMsg.id === data.message_id) {
                        lastMsg.content = streamingMessage.value.content;
                    } else {
                        messages.value.push({ ...streamingMessage.value });
                    }
                    nextTick(scrollToBottom);
                    break;

                case 'llm_response_complete':
                    isStreaming.value = false;
                    const final = messages.value.find(m => m.id === data.message_id);
                    if (final) final.content = data.full_text;
                    break;

                case 'keyphrases_extracted':
                    if (data.keyphrases && data.keyphrases.length > 0) {
                        keyphrases.value[data.message_id || 'latest'] = data.keyphrases;
                    }
                    break;

                case 'alerts_detected':
                    if (data.alerts && data.alerts.length > 0) {
                        data.alerts.forEach(a => alerts.value.push(a));
                    }
                    break;

                case 'pipeline_toggled':
                    pipelineSettings[data.stage] = data.enabled;
                    break;

                case 'error':
                    console.error('Server error:', data.message);
                    isStreaming.value = false;
                    break;
            }
        };

        // --- User Actions ---
        const sendMessage = () => {
            if (!currentMessage.value.trim() || isStreaming.value) return;

            const text = currentMessage.value.trim();
            messages.value.push({
                id: `msg_${messages.value.length}`,
                content: text,
                role: 'user',
                timestamp: new Date().toISOString(),
                goals: []
            });

            isStreaming.value = true;
            sendWs({ type: 'user_message', message: text });
            currentMessage.value = '';
            nextTick(scrollToBottom);
        };

        const togglePipeline = (stage) => {
            const enabled = !pipelineSettings[stage];
            pipelineSettings[stage] = enabled;
            sendWs({ type: 'toggle_pipeline', stage, enabled });
        };

        // --- Goal Controls (wired to backend API) ---
        const toggleGoalLock = async (goal) => {
            const endpoint = goal.locked ? 'unlock' : 'lock';
            const res = await apiCall(
                `/api/conversations/${CONVERSATION_ID}/goals/${goal.id}/${endpoint}`,
                { method: 'POST' }
            );
            if (res?.goal) {
                goal.locked = res.goal.locked;
                const found = goals.value.find(g => g.id === goal.id);
                if (found) found.locked = res.goal.locked;
            }
        };

        const toggleGoalComplete = async (goal) => {
            const res = await apiCall(
                `/api/conversations/${CONVERSATION_ID}/goals/${goal.id}`,
                {
                    method: 'PUT',
                    body: JSON.stringify({ completed: !goal.completed })
                }
            );
            if (res?.goal) {
                goal.completed = res.goal.completed;
                const found = goals.value.find(g => g.id === goal.id);
                if (found) found.completed = res.goal.completed;
            }
        };

        // --- Timeline ---
        const updateTimelineInference = (inferredGoals) => {
            const turnNum = Math.ceil(messages.value.filter(m => m.role === 'user').length);
            let turn = timelineData.value.find(t => t.turnNumber === turnNum);
            if (!turn) {
                turn = { turnNumber: turnNum, inferredGoals: [], finalGoals: [], evaluations: [] };
                timelineData.value.push(turn);
            }
            turn.inferredGoals = inferredGoals || [];
        };

        const updateTimelineMerge = (mergeData) => {
            const turnNum = Math.ceil(messages.value.filter(m => m.role === 'user').length);
            const turn = timelineData.value.find(t => t.turnNumber === turnNum);
            if (turn) {
                turn.finalGoals = (mergeData.goals || []).map(goal => ({
                    ...goal,
                    operation: goal.id.includes('_') ? goal.id.split('_')[1] : 'keep'
                }));
            }
        };

        const updateTimelineEvaluation = (evaluations) => {
            const turnNum = Math.ceil(messages.value.filter(m => m.role === 'assistant').length);
            const turn = timelineData.value.find(t => t.turnNumber === turnNum);
            if (turn) {
                turn.evaluations = (evaluations || []).map(ev => ({
                    goalId: ev.goal_id,
                    result: ev.category,
                    explanation: ev.explanation
                }));
            }
        };

        const getGoalNodeClass = (goal) => {
            return [
                'timeline-node',
                `goal-type-${goal.type}`,
                goal.operation ? `operation-${goal.operation}` : ''
            ].filter(Boolean).join(' ');
        };

        const getConnectionClass = (operation) => `timeline-connection-${operation}`;

        const getEvaluationClass = (result) => `timeline-evaluation-${result} px-2 py-1 rounded text-xs`;

        const getEvaluationIcon = (result) => {
            switch (result) {
                case 'confirm': return '✓';
                case 'contradict': return '✗';
                case 'ignore': return '⊘';
                default: return '?';
            }
        };

        // --- Utilities ---
        const scrollToBottom = () => {
            if (messagesContainer.value) {
                messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
            }
        };

        const formatTime = (timestamp) => {
            return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        };

        const formatMessage = (content) => {
            return content
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 rounded">$1</code>')
                .replace(/\n/g, '<br>');
        };

        const truncateText = (text, max) => {
            if (!text) return '';
            return text.length > max ? text.substring(0, max) + '...' : text;
        };

        const navigateToMessage = (turnNumber) => {
            const userMsgs = messages.value.filter(m => m.role === 'user');
            if (userMsgs[turnNumber - 1]) {
                nextTick(() => {
                    const els = document.querySelectorAll('.chat-message');
                    const idx = (turnNumber - 1) * 2;
                    if (els[idx]) {
                        els[idx].scrollIntoView({ behavior: 'smooth', block: 'center' });
                        els[idx].classList.add('highlighted');
                        setTimeout(() => els[idx].classList.remove('highlighted'), 2000);
                    }
                });
            }
        };

        const scrollTimeline = (dir) => {
            const el = document.querySelector('.timeline-visualization');
            if (el) el.scrollTo({ top: dir === 'top' ? 0 : el.scrollHeight, behavior: 'smooth' });
        };

        // --- Lifecycle ---
        onMounted(() => {
            connectWebSocket();
            fetchLlmStatus();
        });

        return {
            messages, goals, currentMessage, isStreaming, activeTab,
            pipelineSettings, messagesContainer, timelineData, llmStatus,
            selectedGoalId, selectedGoal, keyphrases, allKeyphrases, alerts,
            goalTypeConfig, evalStyleFor,
            sendMessage, togglePipeline, toggleGoalLock, toggleGoalComplete,
            selectGoal, dismissAlert, alertIcon, alertSeverityClass, fetchKeyphrases,
            formatTime, formatMessage, truncateText,
            getGoalNodeClass, getConnectionClass, getEvaluationClass, getEvaluationIcon,
            navigateToMessage, scrollTimeline,
        };
    }
}).mount('#app');