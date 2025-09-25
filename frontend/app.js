/**
 * OnGoal Frontend - Vue.js application with WebSocket integration
 */

const { createApp, ref, reactive, onMounted, nextTick, watch } = Vue;

createApp({
    setup() {
        // Reactive state
        const messages = ref([]);
        const goals = ref([]);
        const currentMessage = ref('');
        const isStreaming = ref(false);
        const activeTab = ref('Goals');
        const ws = ref(null);
        const messagesContainer = ref(null);
        const timelineData = ref([]);  // Timeline visualization data
        
        // Pipeline settings
        const pipelineSettings = reactive({
            infer: true,
            merge: true,
            evaluate: true
        });
        
        // Current streaming message
        const streamingMessage = ref({
            id: '',
            content: '',
            role: 'assistant',
            timestamp: new Date().toISOString()
        });

        // WebSocket connection
        const connectWebSocket = () => {
            try {
                console.log('🔗 DEBUG: Attempting WebSocket connection to ws://localhost:8000/ws');
                ws.value = new WebSocket('ws://localhost:8000/ws');
                
                ws.value.onopen = () => {
                    console.log('✅ DEBUG: WebSocket connected successfully');
                    // Request current conversation state
                    sendWebSocketMessage({
                        type: 'get_conversation'
                    });
                };
                
                ws.value.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                };
                
                ws.value.onclose = () => {
                    console.log('WebSocket disconnected');
                    // Attempt to reconnect after 3 seconds
                    setTimeout(connectWebSocket, 3000);
                };
                
            ws.value.onerror = (error) => {
                console.error('❌ DEBUG: WebSocket error:', error);
            };
                
            } catch (error) {
                console.error('Failed to connect WebSocket:', error);
                // Retry connection after 3 seconds
                setTimeout(connectWebSocket, 3000);
            }
        };

        // Send message via WebSocket
        const sendWebSocketMessage = (data) => {
            console.log('📤 DEBUG: Attempting to send WebSocket message:', data);
            if (ws.value && ws.value.readyState === WebSocket.OPEN) {
                ws.value.send(JSON.stringify(data));
                console.log('✅ DEBUG: WebSocket message sent');
            } else {
                console.error('❌ DEBUG: WebSocket not connected. ReadyState:', ws.value?.readyState);
            }
        };

        // Handle incoming WebSocket messages
        const handleWebSocketMessage = (data) => {
            console.log('🚨 WEBSOCKET MESSAGE:', data.type);
            switch (data.type) {
                case 'conversation_state':
                    // Load existing conversation
                    messages.value = data.conversation.messages;
                    goals.value = data.conversation.goals;
                    Object.assign(pipelineSettings, data.conversation.pipeline_settings);
                    break;
                    
                case 'goals_inferred':
                    console.log('🚨 GOALS_INFERRED handler triggered with:', data.goals);
                    // Add inferred goals to the last user message
                    const lastMessage = messages.value[messages.value.length - 1];
                    if (lastMessage && lastMessage.role === 'user') {
                        lastMessage.goals = data.goals;
                    }
                    
                    // Add goals to global goals list
                    goals.value.push(...data.goals);
                    
                    // Update timeline data with inferred goals
                    console.log('🚨 About to call updateTimelineWithInference...');
                    updateTimelineWithInference(data.goals);
                    console.log('🚨 Called updateTimelineWithInference');
                    break;
                    
                case 'goals_updated':
                    console.log('🔄 DEBUG: Goals updated via merge:', data.goals);
                    // Replace all goals with updated list (handles merge operations)
                    goals.value = [...data.goals];
                    
                    // For multi-turn conversations, we need to update goals on ALL user messages
                    // since merged goals might span multiple messages
                    messages.value.forEach(message => {
                        if (message.role === 'user') {
                            // Find goals that originated from this message
                            const messageGoals = data.goals.filter(goal => 
                                goal.source_message_id === message.id);
                            if (messageGoals.length > 0) {
                                message.goals = messageGoals;
                            }
                        }
                    });
                    
                    // Update timeline data with merge information
                    updateTimelineWithMerge(data);
                    
                    // If no goals were found for the latest message due to merging,
                    // show a subset of all goals as glyphs to indicate activity
                    const lastUserMessage = messages.value.slice().reverse().find(m => m.role === 'user');
                    if (lastUserMessage && (!lastUserMessage.goals || lastUserMessage.goals.length === 0)) {
                        // Show some goals as glyphs to indicate the message contributed to goals
                        // Take the most recent goals (assumes newest goals are at the end)
                        const recentGoals = data.goals.slice(-2); // Show last 2 goals as glyphs
                        lastUserMessage.goals = recentGoals;
                    }
                    break;
                    
                case 'goals_evaluated':
                    console.log('⚖️ DEBUG: Received goal evaluations:', data.evaluations);
                    data.evaluations.forEach(evaluation => {
                        const goal = goals.value.find(g => g.id === evaluation.goal_id);
                        if (goal) {
                            goal.status = evaluation.category;
                            goal.evaluation = evaluation;
                        }
                    });
                    
                    // Update timeline data with evaluation results
                    updateTimelineWithEvaluation(data.evaluations);
                    break;
                    
                case 'llm_response_chunk':
                    // Handle streaming response
                    // Note: isStreaming is already true from sendMessage(), so just handle the content
                    if (streamingMessage.value.id !== data.message_id) {
                        // Start new streaming message
                        streamingMessage.value = {
                            id: data.message_id,
                            content: data.text,
                            role: 'assistant',
                            timestamp: new Date().toISOString()
                        };
                    } else {
                        // Append to existing streaming message
                        streamingMessage.value.content += data.text;
                    }
                    
                    // Update the last assistant message or add new one
                    const lastMsg = messages.value[messages.value.length - 1];
                    if (lastMsg && lastMsg.role === 'assistant' && lastMsg.id === data.message_id) {
                        lastMsg.content = streamingMessage.value.content;
                    } else {
                        messages.value.push({...streamingMessage.value});
                    }
                    
                    // Auto-scroll to bottom
                    nextTick(() => {
                        scrollToBottom();
                    });
                    break;
                    
                case 'llm_response_complete':
                    // Finish streaming
                    isStreaming.value = false;
                    
                    // Update final message
                    const finalMsg = messages.value.find(m => m.id === data.message_id);
                    if (finalMsg) {
                        finalMsg.content = data.full_text;
                    }
                    break;
                    
                case 'pipeline_toggled':
                    // Update pipeline settings
                    pipelineSettings[data.stage] = data.enabled;
                    break;
                    
                case 'error':
                    console.error('Server error:', data.message);
                    isStreaming.value = false;
                    break;
                    
                default:
                    console.log('Unknown message type:', data.type);
            }
        };

        // Send user message
        const sendMessage = () => {
            if (!currentMessage.value.trim() || isStreaming.value) return;
            
            const messageText = currentMessage.value.trim();
            const messageId = `msg_${messages.value.length}`;
            
            // Add user message to chat
            const userMessage = {
                id: messageId,
                content: messageText,
                role: 'user',
                timestamp: new Date().toISOString(),
                goals: []
            };
            
            messages.value.push(userMessage);
            
            // Set streaming immediately to show "Thinking..." indicator
            // This provides instant feedback while backend processes goals and starts LLM response
            isStreaming.value = true;
            
            // Send to backend
            sendWebSocketMessage({
                type: 'user_message',
                message: messageText
            });
            
            // Clear input
            currentMessage.value = '';
            
            // Scroll to bottom
            nextTick(() => {
                scrollToBottom();
            });
        };

        // Toggle pipeline stage
        const togglePipeline = (stage) => {
            const newState = !pipelineSettings[stage];
            pipelineSettings[stage] = newState;
            
            sendWebSocketMessage({
                type: 'toggle_pipeline',
                stage: stage,
                enabled: newState
            });
        };

        // Goal controls
        const toggleGoalLock = (goal) => {
            goal.locked = !goal.locked;
            // Goal lock state persistence (Phase 2 feature)
        };

        const toggleGoalComplete = (goal) => {
            goal.completed = !goal.completed;
            // Goal completion state persistence (Phase 2 feature)
        };

        // Utility functions
        const scrollToBottom = () => {
            if (messagesContainer.value) {
                messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
            }
        };

        const formatTime = (timestamp) => {
            const date = new Date(timestamp);
            return date.toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        };

        const formatMessage = (content) => {
            // Basic markdown-like formatting
            return content
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 rounded">$1</code>')
                .replace(/\n/g, '<br>');
        };

        // Lifecycle
        onMounted(() => {
            connectWebSocket();
            
            // Expose data to window for debugging
            window.ws = ws;
            window.goals = goals;
            window.messages = messages;
            window.pipelineSettings = pipelineSettings;
        });

        // Watch for goal changes to update UI
        watch(goals, (newGoals) => {
            console.log('Goals updated:', newGoals.length);
        }, { deep: true });

        // Timeline functions
        const updateTimelineWithInference = (inferredGoals) => {
            console.log('🚨🚨🚨 TIMELINE INFERENCE CALLED 🚨🚨🚨', inferredGoals);
            const turnNumber = Math.ceil(messages.value.filter(m => m.role === 'user').length);
            console.log('🚨 TIMELINE: Current turn number:', turnNumber);
            
            // Find or create timeline entry for this turn
            let turn = timelineData.value.find(t => t.turnNumber === turnNumber);
            if (!turn) {
                turn = {
                    turnNumber,
                    inferredGoals: [],
                    finalGoals: [],
                    evaluations: []
                };
                timelineData.value.push(turn);
                console.log('➕ Created new timeline turn:', turn);
            }
            
            turn.inferredGoals = inferredGoals || [];
            console.log('🚨 TIMELINE: Updated with inference:', turn);
            console.log('🚨 TIMELINE: Total timeline data length:', timelineData.value.length);
            console.log('🚨 TIMELINE: timelineData.value =', timelineData.value);
        };
        
        const updateTimelineWithMerge = (mergeData) => {
            console.log('🔍 updateTimelineWithMerge called with:', mergeData);
            const turnNumber = Math.ceil(messages.value.filter(m => m.role === 'user').length);
            
            let turn = timelineData.value.find(t => t.turnNumber === turnNumber);
            if (turn) {
                // Add operation information to goals
                turn.finalGoals = (mergeData.goals || []).map(goal => ({
                    ...goal,
                    operation: goal.id.includes('_') ? goal.id.split('_')[1] : 'keep'
                }));
                console.log('📊 Timeline updated with merge:', turn);
                console.log('📊 Total timeline data length:', timelineData.value.length);
            } else {
                console.log('❌ No timeline turn found for merge, turn number:', turnNumber);
            }
        };
        
        const updateTimelineWithEvaluation = (evaluations) => {
            const turnNumber = Math.ceil(messages.value.filter(m => m.role === 'assistant').length);
            
            let turn = timelineData.value.find(t => t.turnNumber === turnNumber);
            if (turn) {
                turn.evaluations = (evaluations || []).map(eval => ({
                    goalId: eval.goal_id,
                    result: eval.category,
                    explanation: eval.explanation
                }));
                console.log('📊 Timeline updated with evaluation:', turn);
            }
        };
        
        const getGoalNodeClass = (goal) => {
            return [
                'timeline-node',
                `goal-type-${goal.type}`,
                goal.operation ? `operation-${goal.operation}` : ''
            ].filter(Boolean).join(' ');
        };
        
        const getConnectionClass = (operation) => {
            return `timeline-connection-${operation}`;
        };
        
        const getEvaluationClass = (result) => {
            return `timeline-evaluation-${result} px-2 py-1 rounded text-xs`;
        };
        
        const getEvaluationIcon = (result) => {
            switch (result) {
                case 'confirm': return '✓';
                case 'contradict': return '✗';
                case 'ignore': return '⊘';
                default: return '?';
            }
        };
        
        const truncateText = (text, maxLength) => {
            if (!text) return '';
            return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
        };
        
        const navigateToMessage = (turnNumber) => {
            // Scroll to the corresponding message in chat
            const userMessages = messages.value.filter(m => m.role === 'user');
            if (userMessages[turnNumber - 1]) {
                // Find the message element and scroll to it
                nextTick(() => {
                    const messageElements = document.querySelectorAll('.chat-message');
                    const targetIndex = (turnNumber - 1) * 2; // User + Assistant message pairs
                    if (messageElements[targetIndex]) {
                        messageElements[targetIndex].scrollIntoView({ 
                            behavior: 'smooth', 
                            block: 'center' 
                        });
                        // Highlight the message briefly
                        messageElements[targetIndex].classList.add('highlighted');
                        setTimeout(() => {
                            messageElements[targetIndex].classList.remove('highlighted');
                        }, 2000);
                    }
                });
            }
        };
        
        const scrollTimeline = (direction) => {
            const timelineContainer = document.querySelector('.timeline-visualization');
            if (timelineContainer) {
                const scrollAmount = direction === 'top' ? 0 : timelineContainer.scrollHeight;
                timelineContainer.scrollTo({ top: scrollAmount, behavior: 'smooth' });
            }
        };

        return {
            // State
            messages,
            goals,
            currentMessage,
            isStreaming,
            activeTab,
            pipelineSettings,
            messagesContainer,
            timelineData,
            
            // Methods
            sendMessage,
            togglePipeline,
            toggleGoalLock,
            toggleGoalComplete,
            formatTime,
            formatMessage,
            updateTimelineWithInference,
            updateTimelineWithMerge,
            updateTimelineWithEvaluation,
            getGoalNodeClass,
            getConnectionClass,
            getEvaluationClass,
            getEvaluationIcon,
            truncateText,
            navigateToMessage,
            scrollTimeline
        };
    }
}).mount('#app');
