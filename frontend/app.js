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
        const toasts = ref([]);
        const goalHistory = ref([]);
        const goalProgress = ref([]);

        const pipelineSettings = reactive({
            infer: true,
            merge: true,
            evaluate: true
        });

        const streamingMessage = ref({
            id: '', content: '', role: 'assistant', timestamp: ''
        });

        const messageGoalMap = ref({});

        const expandedGlyphId = ref(null);

        const highlightedMessageId = ref(null);

        // --- Computed ---
        const individualGoalView = computed(() => {
            return selectedGoalId.value !== null;
        });

        const selectedGoal = computed(() => {
            if (!selectedGoalId.value) return null;
            return goals.value.find(g => g.id === selectedGoalId.value) || null;
        });

        const goalEvaluations = computed(() => {
            if (!selectedGoalId.value) return [];
            const evals = [];
            messages.value.forEach(msg => {
                if (msg.role === 'assistant') {
                    const mapped = messageGoalMap.value[msg.id] || [];
                    const goalEval = mapped.find(g => g.id === selectedGoalId.value);
                    if (goalEval?.evaluation) {
                        evals.push({
                            messageId: msg.id,
                            category: goalEval.evaluation.category,
                            explanation: goalEval.evaluation.explanation,
                            examples: goalEval.evaluation.examples || [],
                            timestamp: msg.timestamp,
                            turnNumber: evals.length + 1,
                        });
                    }
                }
            });
            return evals;
        });

        const filteredMessages = computed(() => {
            if (!selectedGoalId.value) return messages.value;
            return messages.value.filter(msg => {
                if (msg.role === 'user') return true;
                const mapped = messageGoalMap.value[msg.id] || [];
                return mapped.some(g => g.id === selectedGoalId.value);
            });
        });

        const allKeyphrases = computed(() => {
            const all = [];
            Object.values(keyphrases.value).forEach(phrases => {
                all.push(...phrases);
            });
            return [...new Set(all)];
        });

        const keyphraseFrequency = computed(() => {
            const freq = {};
            Object.values(keyphrases.value).forEach(phrases => {
                phrases.forEach(p => {
                    freq[p] = (freq[p] || 0) + 1;
                });
            });
            return freq;
        });

        const sharedKeyphrases = computed(() => {
            return Object.entries(keyphraseFrequency.value)
                .filter(([, count]) => count > 1)
                .map(([phrase]) => phrase);
        });

        const uniqueKeyphrases = computed(() => {
            return Object.entries(keyphraseFrequency.value)
                .filter(([, count]) => count === 1)
                .map(([phrase]) => phrase);
        });

        const goalProgressMap = computed(() => {
            const map = {};
            goalProgress.value.forEach(p => {
                map[p.goal_id] = p;
            });
            return map;
        });

        const progressStatusStyle = (status) => {
            switch (status) {
                case 'completed_manual': return 'bg-green-200 text-green-900';
                case 'likely_complete': return 'bg-emerald-100 text-emerald-800';
                case 'progressing': return 'bg-blue-100 text-blue-800';
                case 'at_risk': return 'bg-amber-100 text-amber-800';
                case 'contradicted': return 'bg-red-100 text-red-800';
                case 'active': return 'bg-gray-100 text-gray-800';
                default: return 'bg-gray-100 text-gray-800';
            }
        };

        const progressStatusLabel = (status) => {
            switch (status) {
                case 'completed_manual': return 'Completed';
                case 'likely_complete': return 'Likely Complete';
                case 'progressing': return 'Progressing';
                case 'at_risk': return 'At Risk';
                case 'contradicted': return 'Contradicted';
                case 'active': return 'Active';
                default: return status;
            }
        };

        const goalMessageCount = (goalId) => {
            let count = 0;
            messages.value.forEach(msg => {
                if (msg.role === 'assistant') {
                    const mapped = messageGoalMap.value[msg.id] || [];
                    if (mapped.some(g => g.id === goalId)) count++;
                }
            });
            return count;
        };

        const goalTypeConfig = (type) => GOAL_TYPES[type] || GOAL_TYPES.suggestion;
        const evalStyleFor = (status) => EVAL_STYLES[status] || EVAL_STYLES.ignore;

        const goalsForMessage = (msgId, role) => {
            const mapped = messageGoalMap.value[msgId];
            if (mapped) return mapped;
            if (role === 'user') {
                return goals.value.filter(g => g.source_message_id === msgId);
            }
            return [];
        };

        const glyphColor = (goal) => {
            if (!goal.status) return 'bg-gray-300';
            if (goal.status === 'confirm') return 'bg-green-500';
            if (goal.status === 'contradict') return 'bg-red-500';
            if (goal.status === 'ignore') return 'bg-yellow-500';
            return 'bg-gray-300';
        };

        const toggleGlyph = (goalId) => {
            expandedGlyphId.value = expandedGlyphId.value === goalId ? null : goalId;
        };

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

        const dismissAllAlerts = () => {
            alerts.value = [];
        };

        const dismissToast = (index) => {
            toasts.value.splice(index, 1);
        };

        const pushToast = (alert) => {
            const toast = {
                id: Date.now() + Math.random(),
                severity: alert.severity,
                title: alert.alert_type.charAt(0).toUpperCase() + alert.alert_type.slice(1),
                message: alert.message || 'Alert detected',
            };
            toasts.value.push(toast);
            setTimeout(() => {
                const idx = toasts.value.findIndex(t => t.id === toast.id);
                if (idx !== -1) toasts.value.splice(idx, 1);
            }, 6000);
        };

        const alertIcon = (type) => {
            switch (type) {
                case 'forgetting': return '🧠';
                case 'contradiction': return '⚡';
                case 'derailment': return '🚂';
                case 'repetition': return '🔄';
                case 'fixation': return '🎯';
                case 'breakdown': return '💬';
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
                    goalHistory.value = data.conversation.goal_history || [];
                    goalProgress.value = data.conversation.goal_progress || [];
                    if (data.conversation.pipeline_settings) {
                        const ps = data.conversation.pipeline_settings;
                        pipelineSettings.infer = ps.infer ?? ps.infer ?? true;
                        pipelineSettings.merge = ps.merge ?? true;
                        pipelineSettings.evaluate = ps.evaluate ?? true;
                    }
                    // Rebuild per-message goal map from stored data
                    messageGoalMap.value = {};
                    data.conversation.messages.forEach(msg => {
                        if (msg.role === 'user' && msg.goals && msg.goals.length) {
                            messageGoalMap.value[msg.id] = msg.goals;
                        }
                    });
                    // Map evaluated goals to assistant messages
                    const assistantMsgs = data.conversation.messages.filter(m => m.role === 'assistant');
                    data.conversation.goals.forEach(goal => {
                        if (goal.evaluation && goal.source_message_id) {
                            const userMsgIdx = data.conversation.messages.findIndex(m => m.id === goal.source_message_id);
                            if (userMsgIdx >= 0) {
                                const assistantMsg = assistantMsgs.find((_, i) => {
                                    const aIdx = data.conversation.messages.indexOf(assistantMsgs[i]);
                                    return aIdx > userMsgIdx;
                                });
                                if (assistantMsg) {
                                    if (!messageGoalMap.value[assistantMsg.id]) {
                                        messageGoalMap.value[assistantMsg.id] = [];
                                    }
                                    if (!messageGoalMap.value[assistantMsg.id].find(g => g.id === goal.id)) {
                                        messageGoalMap.value[assistantMsg.id].push(goal);
                                    }
                                }
                            }
                        }
                    });
                    break;

                case 'goals_inferred': {
                    const last = messages.value[messages.value.length - 1];
                    if (last?.role === 'user') last.goals = data.goals;
                    goals.value.push(...data.goals);
                    if (data.message_id) {
                        messageGoalMap.value[data.message_id] = [...data.goals];
                    }
                    updateTimelineInference(data.goals);
                    break;
                }

                case 'goals_updated':
                    goals.value = [...data.goals];
                    messages.value.forEach(msg => {
                        if (msg.role === 'user') {
                            const msgGoals = data.goals.filter(g => g.source_message_id === msg.id);
                            msg.goals = msgGoals;
                            if (msgGoals.length > 0) {
                                messageGoalMap.value[msg.id] = msgGoals;
                            } else {
                                delete messageGoalMap.value[msg.id];
                            }
                        }
                    });
                    fetchGoalHistory();
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
                    if (data.message_id) {
                        messageGoalMap.value[data.message_id] = data.evaluations.map(ev => {
                            const goal = goals.value.find(g => g.id === ev.goal_id);
                            return goal || { id: ev.goal_id, status: ev.category, evaluation: ev };
                        });
                    }
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
                        data.alerts.forEach(a => {
                            alerts.value.push(a);
                            pushToast(a);
                        });
                    }
                    break;

                case 'goal_progress_updated':
                    if (data.progress) {
                        goalProgress.value = data.progress;
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

        const highlightModes = reactive({
            keyphrases: false,
            similarSentences: false,
            uniqueSentences: false,
        });

        const similarSentences = ref([]);
        const uniqueSentences = ref([]);

        const fetchSentenceSimilarity = async () => {
            const data = await apiCall(`/api/conversations/${CONVERSATION_ID}/sentence-similarity`);
            if (data) {
                similarSentences.value = data.similar_sentences || [];
                uniqueSentences.value = data.unique_sentences || [];
            }
        };

        const showGoalHistory = ref(false);

        const fetchGoalHistory = async () => {
            const data = await apiCall(`/api/conversations/${CONVERSATION_ID}/goal-history`);
            if (data?.goal_history) {
                goalHistory.value = data.goal_history;
            }
        };

        const fetchGoalProgress = async () => {
            const data = await apiCall(`/api/conversations/${CONVERSATION_ID}/goal-progress`);
            if (data?.progress) {
                goalProgress.value = data.progress;
            }
        };

        const restoreGoal = async (entryIndex) => {
            const res = await apiCall(
                `/api/conversations/${CONVERSATION_ID}/goal-history/${entryIndex}/restore`,
                { method: 'POST' }
            );
            if (res?.goal) {
                const found = goals.value.find(g => g.id === res.goal.id);
                if (found) {
                    found.text = res.goal.text;
                    found.type = res.goal.type;
                } else {
                    goals.value.push(res.goal);
                }
                await fetchGoalHistory();
            }
        };

        const getExpandedEvaluation = () => {
            if (!expandedGlyphId.value) return null;
            for (const msg of messages.value) {
                if (msg.role === 'assistant') {
                    const g = goalsForMessage(msg.id, 'assistant').find(g => g.id === expandedGlyphId.value);
                    if (g?.evaluation) return g.evaluation;
                }
            }
            return null;
        };

        const formatMessage = (content, messageId, role) => {
            let text = content;
            let markers = [];

            const pushHighlight = (phrase, category) => {
                const escaped = phrase.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                const markerId = `§M${markers.length}§`;
                const cssClass =
                    category === 'confirm' ? 'hl-confirm' :
                    category === 'contradict' ? 'hl-contradict' :
                    category === 'ignore' ? 'hl-ignore' :
                    category === 'keyphrase' ? 'hl-keyphrase' :
                    category === 'keyphrase-shared' ? 'hl-keyphrase-shared' :
                    category === 'keyphrase-unique' ? 'hl-keyphrase-unique' :
                    category === 'similar-sentence' ? 'hl-similar-sentence' :
                    category === 'unique-sentence' ? 'hl-unique-sentence' : '';
                markers.push({ markerId, cssClass });
                try {
                    text = text.replace(new RegExp(`(#{1,6}\\s+)?(${escaped})`, 'g'), `${markerId}$1$2§/M§`);
                } catch (_) {}
            };

            if (role === 'assistant' && (expandedGlyphId.value || individualGoalView.value)) {
                const targetGoalId = expandedGlyphId.value || selectedGoalId.value;
                const mapped = messageGoalMap.value[messageId] || [];
                const goalEval = mapped.find(g => g.id === targetGoalId);
                if (goalEval?.evaluation?.examples?.length) {
                    goalEval.evaluation.examples.forEach(example => pushHighlight(example, goalEval.evaluation.category));
                }
            }

            if (role === 'assistant' && highlightModes.keyphrases) {
                sharedKeyphrases.value.forEach(kp => pushHighlight(kp, 'keyphrase-shared'));
                uniqueKeyphrases.value.forEach(kp => pushHighlight(kp, 'keyphrase-unique'));
            }

            if (role === 'assistant' && highlightModes.similarSentences) {
                similarSentences.value.forEach(group => {
                    (group.sentences || []).forEach(s => {
                        if (s.message_id === messageId && s.text) {
                            pushHighlight(s.text, 'similar-sentence');
                        }
                    });
                });
            }

            if (role === 'assistant' && highlightModes.uniqueSentences) {
                uniqueSentences.value.forEach(s => {
                    if (s.message_id === messageId && s.text) {
                        pushHighlight(s.text, 'unique-sentence');
                    }
                });
            }

            let html = text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 rounded">$1</code>')
                .replace(/\n/g, '<br>');

            markers.forEach(({ markerId, cssClass }) => {
                html = html
                    .replace(new RegExp(markerId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'),
                        `<mark class="${cssClass}">`)
                    .replace(/§\/M§/g, '</mark>');
            });

            return html;
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

        const exitIndividualView = () => {
            selectedGoalId.value = null;
            highlightedMessageId.value = null;
        };

        const scrollToEvalMessage = (messageId) => {
            highlightedMessageId.value = messageId;
            nextTick(() => {
                const el = document.querySelector(`[data-msg-id="${messageId}"]`);
                if (el) {
                    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    el.classList.add('highlighted');
                    setTimeout(() => {
                        el.classList.remove('highlighted');
                        highlightedMessageId.value = null;
                    }, 2500);
                }
            });
        };

        // --- D3 Timeline Rendering ---
        const renderTimeline = () => {
            nextTick(() => {
                const container = document.querySelector('#d3-timeline');
                if (!container || timelineData.value.length === 0) return;

                container.innerHTML = '';
                const containerWidth = container.clientWidth || 280;
                const rowHeight = 50;
                const turnGap = 60;
                const headerHeight = 24;
                const nodeWidth = 60;
                const nodeHeight = 28;
                const nodePadding = 8;

                const turns = timelineData.value;
                const totalHeight = turns.length * (3 * rowHeight + turnGap) + 40;
                
                const svg = d3.select(container)
                    .append('svg')
                    .attr('width', containerWidth)
                    .attr('height', totalHeight);

                let yOffset = 0;

                turns.forEach((turn, turnIdx) => {
                    const turnGroup = svg.append('g')
                        .attr('class', 'timeline-turn-group')
                        .attr('transform', `translate(0, ${yOffset})`);

                    turnGroup.append('text')
                        .attr('x', 4)
                        .attr('y', 14)
                        .attr('class', 'text-xs font-bold fill-gray-700')
                        .text(`Turn ${turn.turnNumber}`);

                    const inferY = headerHeight;
                    const mergeY = inferY + rowHeight;
                    const evalY = mergeY + rowHeight;

                    turnGroup.append('text')
                        .attr('x', 4).attr('y', inferY + 14)
                        .attr('class', 'text-xs fill-blue-500')
                        .text('Infer');

                    turnGroup.append('text')
                        .attr('x', 4).attr('y', mergeY + 14)
                        .attr('class', 'text-xs fill-green-600')
                        .text('Merge');

                    turnGroup.append('text')
                        .attr('x', 4).attr('y', evalY + 14)
                        .attr('class', 'text-xs fill-purple-600')
                        .text('Evaluate');

                    const colStart = 60;
                    const colWidth = containerWidth - colStart - 8;

                    const inferGoals = turn.inferredGoals || [];
                    const finalGoals = turn.finalGoals || [];
                    const evaluations = turn.evaluations || [];

                    const inferSpacing = inferGoals.length > 1 ? colWidth / inferGoals.length : 0;
                    const mergeSpacing = finalGoals.length > 1 ? colWidth / finalGoals.length : 0;
                    const evalSpacing = evaluations.length > 1 ? colWidth / evaluations.length : 0;

                    const inferPositions = [];
                    inferGoals.forEach((goal, i) => {
                        const x = colStart + (inferSpacing > 0 ? inferSpacing * i + inferSpacing / 2 : colWidth / 2);
                        inferPositions.push({ x, goal });
                        turnGroup.append('g')
                            .attr('transform', `translate(${x - nodeWidth/2}, ${inferY})`)
                            .append('rect')
                            .attr('width', nodeWidth).attr('height', nodeHeight)
                            .attr('rx', 4).attr('fill', '#dbeafe').attr('stroke', '#93c5fd').attr('stroke-width', 1);
                        turnGroup.append('g')
                            .attr('transform', `translate(${x - nodeWidth/2}, ${inferY})`)
                            .append('text')
                            .attr('x', nodeWidth/2).attr('y', nodeHeight/2 + 4)
                            .attr('text-anchor', 'middle')
                            .attr('class', 'text-xs fill-blue-800')
                            .text(truncateText(goal.id + ': ' + goal.text, 12));
                    });

                    const mergePositions = [];
                    finalGoals.forEach((goal, i) => {
                        const x = colStart + (mergeSpacing > 0 ? mergeSpacing * i + mergeSpacing / 2 : colWidth / 2);
                        mergePositions.push({ x, goal });
                        const opColor = goal.operation === 'combine' ? '#fde68a' : goal.operation === 'replace' ? '#fecaca' : '#d1fae5';
                        const opStroke = goal.operation === 'combine' ? '#f59e0b' : goal.operation === 'replace' ? '#ef4444' : '#10b981';
                        turnGroup.append('g')
                            .attr('transform', `translate(${x - nodeWidth/2}, ${mergeY})`)
                            .append('rect')
                            .attr('width', nodeWidth).attr('height', nodeHeight)
                            .attr('rx', 4).attr('fill', opColor).attr('stroke', opStroke).attr('stroke-width', 1.5);
                        turnGroup.append('g')
                            .attr('transform', `translate(${x - nodeWidth/2}, ${mergeY})`)
                            .append('text')
                            .attr('x', nodeWidth/2).attr('y', nodeHeight/2 + 4)
                            .attr('text-anchor', 'middle')
                            .attr('class', 'text-xs fill-gray-800')
                            .text(truncateText(goal.id, 12));
                    });

                    const evalPositions = [];
                    evaluations.forEach((ev, i) => {
                        const x = colStart + (evalSpacing > 0 ? evalSpacing * i + evalSpacing / 2 : colWidth / 2);
                        evalPositions.push({ x, ev });
                        const evColor = ev.result === 'confirm' ? '#dcfce7' : ev.result === 'contradict' ? '#fee2e2' : '#fef3c7';
                        const evStroke = ev.result === 'confirm' ? '#22c55e' : ev.result === 'contradict' ? '#ef4444' : '#eab308';
                        const icon = ev.result === 'confirm' ? '✓' : ev.result === 'contradict' ? '✗' : '⊘';
                        turnGroup.append('g')
                            .attr('transform', `translate(${x - nodeWidth/2}, ${evalY})`)
                            .append('rect')
                            .attr('width', nodeWidth).attr('height', nodeHeight)
                            .attr('rx', 4).attr('fill', evColor).attr('stroke', evStroke).attr('stroke-width', 1.5);
                        turnGroup.append('g')
                            .attr('transform', `translate(${x - nodeWidth/2}, ${evalY})`)
                            .append('text')
                            .attr('x', nodeWidth/2).attr('y', nodeHeight/2 + 4)
                            .attr('text-anchor', 'middle')
                            .attr('class', 'text-xs')
                            .attr('fill', evStroke)
                            .text(`${icon} ${ev.goalId}`);
                    });

                    inferPositions.forEach(inf => {
                        const bestMerge = mergePositions.length === 1 ? mergePositions[0] :
                            mergePositions.find(m => m.goal.id === inf.goal.id) || mergePositions[0];
                        if (bestMerge) {
                            turnGroup.append('path')
                                .attr('d', `M${inf.x},${inferY + nodeHeight} C${inf.x},${inferY + nodeHeight + 10} ${bestMerge.x},${mergeY - 10} ${bestMerge.x},${mergeY}`)
                                .attr('fill', 'none')
                                .attr('stroke', '#93c5fd')
                                .attr('stroke-width', 1.5)
                                .attr('stroke-dasharray', '4,2');
                        }
                    });

                    mergePositions.forEach(mrg => {
                        const bestEval = evalPositions.length === 1 ? evalPositions[0] :
                            evalPositions.find(e => e.ev.goalId === mrg.goal.id) || evalPositions[0];
                        if (bestEval) {
                            const evalColor = bestEval.ev.result === 'confirm' ? '#22c55e' : bestEval.ev.result === 'contradict' ? '#ef4444' : '#eab308';
                            turnGroup.append('path')
                                .attr('d', `M${mrg.x},${mergeY + nodeHeight} C${mrg.x},${mergeY + nodeHeight + 10} ${bestEval.x},${evalY - 10} ${bestEval.x},${evalY}`)
                                .attr('fill', 'none')
                                .attr('stroke', evalColor)
                                .attr('stroke-width', 1.5);
                        }
                    });

                    yOffset += 3 * rowHeight + turnGap;
                });
            });
        };

        // --- Lifecycle ---
        onMounted(() => {
            connectWebSocket();
            fetchLlmStatus();
        });

        watch(activeTab, (tab) => {
            if (tab === 'Timeline') {
                nextTick(() => setTimeout(renderTimeline, 100));
            }
        });

        watch(timelineData, () => {
            if (activeTab.value === 'Timeline') {
                nextTick(() => setTimeout(renderTimeline, 100));
            }
        }, { deep: true });

        return {
            messages, goals, currentMessage, isStreaming, activeTab,
            pipelineSettings, messagesContainer, timelineData, llmStatus,
            selectedGoalId, selectedGoal, individualGoalView, filteredMessages,
            goalEvaluations,
            keyphrases, allKeyphrases,
            sharedKeyphrases, uniqueKeyphrases,
            alerts, toasts, highlightedMessageId,
            goalHistory, showGoalHistory,
            goalProgress, goalProgressMap, progressStatusStyle, progressStatusLabel,
            goalMessageCount,
            messageGoalMap, expandedGlyphId, highlightModes,
            goalTypeConfig, evalStyleFor, goalsForMessage, glyphColor, toggleGlyph,
            sendMessage, togglePipeline, toggleGoalLock, toggleGoalComplete,
            selectGoal, dismissAlert, dismissAllAlerts, dismissToast, pushToast,
            alertIcon, alertSeverityClass, fetchKeyphrases,
            fetchGoalHistory, restoreGoal, fetchGoalProgress,
            similarSentences, uniqueSentences, fetchSentenceSimilarity,
            formatTime, formatMessage, truncateText,
            getGoalNodeClass, getConnectionClass, getEvaluationClass, getEvaluationIcon,
            navigateToMessage, scrollTimeline,
            exitIndividualView, scrollToEvalMessage,
            renderTimeline,
        };
    }
}).mount('#app');