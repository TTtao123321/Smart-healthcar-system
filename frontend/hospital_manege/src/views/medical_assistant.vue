<template>
	<div class="medical-assistant">
		<!-- 左侧：聊天区域 -->
		<div class="chat-panel">
			<div class="chat-header">
				<div class="header-indicator"></div>
				<span class="header-title">医疗助手</span>
				<span class="header-subtitle">信息查询 · 院内办公</span>
			</div>
			<div class="chat-messages" ref="messagesContainer">
				<!-- 初始问候（无用户提问的助手消息） -->
				<div v-if="greetingMessage" class="greeting-block">
					<div class="greeting-avatar">
						<span>医</span>
					</div>
					<div class="greeting-content">
						<div class="greeting-name">飞码医疗助手</div>
						<div class="greeting-text">{{ greetingMessage.content }}</div>
					</div>
				</div>
				<!-- 对话轮次 -->
				<div
					v-for="(turn, tIdx) in dialogueTurns"
					:key="tIdx"
					class="message-turn"
				>
					<div class="turn-label">
						<span class="turn-label__line"></span>
						<span class="turn-label__text">第{{ tIdx + 1 }}轮对话</span>
						<span class="turn-label__line"></span>
					</div>
					<div
						v-for="(msg, mIdx) in turn"
						:key="mIdx"
						:class="['message-row', msg.role === 'user' ? 'message-row--user' : 'message-row--assistant']"
					>
						<div class="avatar" :class="msg.role === 'user' ? 'avatar--user' : 'avatar--assistant'">
							<span v-if="msg.role === 'assistant'">医</span>
							<span v-else>我</span>
						</div>
						<div class="message-bubble" :class="msg.role === 'user' ? 'bubble--user' : 'bubble--assistant'">
							{{ msg.content }}
						</div>
					</div>
				</div>
				<div v-if="isTyping" class="message-row message-row--assistant">
					<div class="avatar avatar--assistant"><span>医</span></div>
					<div class="message-bubble bubble--assistant typing-bubble">
						<span class="typing-dot"></span>
						<span class="typing-dot"></span>
						<span class="typing-dot"></span>
					</div>
				</div>
			</div>
			<div class="chat-input-area">
				<div class="input-wrapper">
					<el-input
						v-model="inputText"
						placeholder="输入科室、医生或患者信息进行查询..."
						@keyup.enter="sendMessage"
						:disabled="isTyping"
						resize="none"
						type="textarea"
						:autosize="{ minRows: 1, maxRows: 4 }"
					/>
					<el-button
						type="primary"
						:disabled="!inputText.trim() || isTyping"
						@click="sendMessage"
						class="send-btn"
					>
						发送
					</el-button>
				</div>
				<div class="input-hints">
					<span class="hint-tag" v-for="hint in quickHints" :key="hint" @click="inputText = hint">{{ hint }}</span>
				</div>
			</div>
		</div>

		<!-- 右侧：对话记录 -->
		<div class="history-panel">
			<div class="history-header">
				<div class="header-indicator"></div>
				<span class="header-title">对话记录</span>
			</div>
			<div class="history-list">
				<div
					v-for="(conv, index) in conversations"
					:key="index"
					:class="['history-item', index === activeConvIndex ? 'history-item--active' : '']"
					@click="switchConversation(index)"
				>
					<div class="history-item__icon">
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
						</svg>
					</div>
					<div class="history-item__info">
						<div class="history-item__title">{{ conv.title }}</div>
						<div class="history-item__time">{{ conv.time }}</div>
					</div>
					<div class="history-item__actions">
						<span class="history-item__count">{{ conv.messages.length }}</span>
						<span class="history-item__delete" @click.stop="deleteConversation(index)">
							<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<polyline points="3 6 5 6 21 6"/>
								<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
							</svg>
						</span>
					</div>
				</div>
			</div>
			<div class="history-footer">
				<el-button type="primary" plain @click="newConversation" class="new-chat-btn">
					+ 新建对话
				</el-button>
			</div>
		</div>
	</div>
</template>

<script>
import { ElMessage } from 'element-plus';
export default {
	data() {
		return {
			inputText: '',
			isTyping: false,
			activeConvIndex: 0,
			quickHints: ['查询心内科诊室', '查找张医生的出诊信息', '查询患者李明的记录', '门诊日程安排'],
			conversations: [
				{
					title: '院内查询',
					time: '刚刚',
					messages: [
						{ role: 'assistant', content: '您好！我是飞码医疗助手，可以为您提供以下服务：\n\n1. 医院信息问答 — 科室介绍、诊室分布、就诊流程等\n2. 诊室查询 — 按科室名称查询诊室信息与排班\n3. 医生查询 — 查找医生出诊信息、所属科室、诊费标准\n4. 患者查询 — 按姓名或编号查询患者就诊记录\n\n请问您需要查询什么？' }
					]
				}
			]
		};
	},
	computed: {
		currentMessages() {
			return this.conversations[this.activeConvIndex]?.messages || [];
		},
		greetingMessage() {
			const msgs = this.currentMessages;
			if (msgs.length > 0 && msgs[0].role === 'assistant') {
				return msgs[0];
			}
			return null;
		},
		dialogueTurns() {
			const msgs = this.currentMessages;
			if (!msgs.length) return [];
			// 跳过开头的助手问候消息
			const start = msgs[0].role === 'assistant' ? 1 : 0;
			const dialogueMsgs = msgs.slice(start);
			if (!dialogueMsgs.length) return [];
			const turns = [];
			let currentTurn = [];
			dialogueMsgs.forEach((msg) => {
				if (msg.role === 'user' && currentTurn.length > 0) {
					turns.push(currentTurn);
					currentTurn = [];
				}
				currentTurn.push(msg);
			});
			if (currentTurn.length > 0) turns.push(currentTurn);
			return turns;
		}
	},
	methods: {
		sendMessage() {
			const text = this.inputText.trim();
			if (!text || this.isTyping) return;

			const conv = this.conversations[this.activeConvIndex];
			conv.messages.push({ role: 'user', content: text });
			this.inputText = '';
			this.isTyping = true;

			this.$nextTick(() => this.scrollToBottom());

			setTimeout(() => {
				conv.messages.push({
					role: 'assistant',
					content: '正在为您查询相关信息，请稍候……如需更详细的数据，建议您前往对应管理模块查看。'
				});
				this.isTyping = false;
				this.$nextTick(() => this.scrollToBottom());
			}, 1200);
		},
		switchConversation(index) {
			this.activeConvIndex = index;
			this.$nextTick(() => this.scrollToBottom());
		},
		deleteConversation(index) {
			if (this.conversations.length <= 1) {
				return ElMessage.warning('至少保留一条对话记录');
			}
			this.conversations.splice(index, 1);
			if (this.activeConvIndex >= this.conversations.length) {
				this.activeConvIndex = this.conversations.length - 1;
			} else if (this.activeConvIndex > index) {
				this.activeConvIndex--;
			} else if (this.activeConvIndex === index) {
				this.activeConvIndex = 0;
			}
			this.$nextTick(() => this.scrollToBottom());
		},
		newConversation() {
			this.conversations.unshift({
				title: '新对话',
				time: '刚刚',
				messages: [
					{ role: 'assistant', content: '您好！我是飞码医疗助手，可以为您提供医院信息问答、诊室/医生/患者查询等服务。请问您需要查询什么？' }
				]
			});
			this.activeConvIndex = 0;
		},
		scrollToBottom() {
			const container = this.$refs.messagesContainer;
			if (container) {
				container.scrollTop = container.scrollHeight;
			}
		}
	}
};
</script>

<style lang="less" scoped>
@blue-50: #e8f4fd;
@blue-100: #b8dffa;
@blue-200: #8cc8f5;
@blue-400: #3a9fe5;
@blue-500: #1a8cd8;
@blue-600: #0d6ebd;
@blue-700: #0a5a9e;
@blue-800: #084a82;
@white: #ffffff;
@gray-50: #f7f9fc;
@gray-100: #eef2f7;
@gray-200: #dde4ed;
@gray-400: #9ba8b9;
@gray-500: #6b7a8d;
@gray-600: #4a5568;

.medical-assistant {
	display: flex;
	height: calc(100vh - 160px);
	min-height: 500px;
	background: @white;
	overflow: hidden;
	font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}

/* ====== 左侧聊天面板 ====== */
.chat-panel {
	flex: 1;
	display: flex;
	flex-direction: column;
	border-right: 1px solid @gray-100;
	min-width: 0;
}

.chat-header {
	display: flex;
	align-items: center;
	gap: 10px;
	padding: 16px 24px;
	background: linear-gradient(135deg, @blue-500 0%, @blue-700 100%);
	color: @white;

	.header-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: #5dfdcf;
		box-shadow: 0 0 8px rgba(93, 253, 207, 0.6);
		animation: pulse 2s infinite;
	}
	.header-title {
		font-size: 16px;
		font-weight: 600;
		letter-spacing: 0.5px;
	}
	.header-subtitle {
		font-size: 12px;
		opacity: 0.7;
		margin-left: auto;
		letter-spacing: 1px;
	}
}

@keyframes pulse {
	0%, 100% { opacity: 1; }
	50% { opacity: 0.5; }
}

/* 消息列表 */
.chat-messages {
	flex: 1;
	overflow-y: auto;
	padding: 16px 20px;
	background: @gray-50;

	&::-webkit-scrollbar {
		width: 5px;
	}
	&::-webkit-scrollbar-thumb {
		background: @gray-200;
		border-radius: 3px;
	}
}

/* 初始问候区块 */
.greeting-block {
	display: flex;
	gap: 14px;
	padding: 18px 20px;
	margin-bottom: 16px;
	border: 1.5px solid @blue-100;
	border-radius: 14px;
	background: linear-gradient(135deg, @blue-50, @white);
	box-shadow: 0 2px 10px rgba(26, 140, 216, 0.08);
}
.greeting-avatar {
	width: 44px;
	height: 44px;
	border-radius: 12px;
	background: linear-gradient(135deg, @blue-400, @blue-600);
	color: @white;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 16px;
	font-weight: 700;
	flex-shrink: 0;
}
.greeting-content {
	flex: 1;
	min-width: 0;
}
.greeting-name {
	font-size: 14px;
	font-weight: 600;
	color: @blue-700;
	margin-bottom: 6px;
}
.greeting-text {
	font-size: 13px;
	color: @gray-500;
	line-height: 1.8;
	white-space: pre-line;
}

/* 对话轮次容器 */
.message-turn {
	border: 1px solid @blue-100;
	border-radius: 12px;
	padding: 14px 16px 6px;
	margin-bottom: 16px;
	background: @white;
	box-shadow: 0 1px 6px rgba(26, 140, 216, 0.06);
	transition: border-color 0.2s;

	&:hover {
		border-color: @blue-200;
	}

	.message-row:last-child {
		margin-bottom: 8px;
	}
}

/* 轮次标签 */
.turn-label {
	display: flex;
	align-items: center;
	gap: 8px;
	margin-bottom: 12px;

	&__line {
		flex: 1;
		height: 1px;
		background: linear-gradient(90deg, transparent, @blue-100, transparent);
	}
	&__text {
		font-size: 11px;
		color: @blue-400;
		white-space: nowrap;
		letter-spacing: 0.5px;
	}
}

.message-row {
	display: flex;
	align-items: flex-start;
	margin-bottom: 18px;
	animation: fadeInUp 0.3s ease;

	&--user {
		flex-direction: row-reverse;
	}
}

@keyframes fadeInUp {
	from { opacity: 0; transform: translateY(8px); }
	to { opacity: 1; transform: translateY(0); }
}

.avatar {
	width: 36px;
	height: 36px;
	border-radius: 10px;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 13px;
	font-weight: 600;
	flex-shrink: 0;

	&--assistant {
		background: linear-gradient(135deg, @blue-400, @blue-600);
		color: @white;
	}
	&--user {
		background: @gray-200;
		color: @gray-600;
	}
}

.message-bubble {
	max-width: 70%;
	padding: 12px 16px;
	border-radius: 14px;
	font-size: 14px;
	line-height: 1.7;
	word-break: break-word;

	&--assistant {
		margin-left: 10px;
		background: @white;
		color: @gray-600;
		border: 1px solid @gray-100;
		border-top-left-radius: 4px;
		box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
	}
	&--user {
		margin-right: 10px;
		background: linear-gradient(135deg, @blue-500, @blue-600);
		color: @white;
		border-top-right-radius: 4px;
	}
}

/* 打字动画 */
.typing-bubble {
	display: flex;
	align-items: center;
	gap: 5px;
	padding: 14px 20px;
}
.typing-dot {
	width: 7px;
	height: 7px;
	border-radius: 50%;
	background: @blue-400;
	animation: typingBounce 1.2s infinite;
	&:nth-child(2) { animation-delay: 0.2s; }
	&:nth-child(3) { animation-delay: 0.4s; }
}
@keyframes typingBounce {
	0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
	30% { transform: translateY(-6px); opacity: 1; }
}

/* 输入区域 */
.chat-input-area {
	padding: 16px 24px 12px;
	background: @white;
	border-top: 1px solid @gray-100;
}

.input-wrapper {
	display: flex;
	gap: 10px;
	align-items: flex-end;

	:deep(.el-textarea__inner) {
		border-radius: 10px;
		border: 1.5px solid @gray-200;
		padding: 10px 14px;
		font-size: 14px;
		transition: border-color 0.2s;
		&:focus {
			border-color: @blue-400;
			box-shadow: 0 0 0 2px rgba(58, 159, 229, 0.12);
		}
	}

	.send-btn {
		height: 40px;
		border-radius: 10px;
		padding: 0 22px;
		font-weight: 500;
		background: linear-gradient(135deg, @blue-500, @blue-600);
		border: none;
		transition: all 0.2s;
		&:hover:not(:disabled) {
			background: linear-gradient(135deg, @blue-400, @blue-500);
			transform: translateY(-1px);
			box-shadow: 0 4px 12px rgba(26, 140, 216, 0.3);
		}
		&:disabled {
			opacity: 0.5;
		}
	}
}

.input-hints {
	display: flex;
	gap: 8px;
	margin-top: 10px;
	flex-wrap: wrap;
}

.hint-tag {
	font-size: 12px;
	padding: 4px 12px;
	border-radius: 20px;
	background: @blue-50;
	color: @blue-600;
	cursor: pointer;
	transition: all 0.2s;
	border: 1px solid transparent;
	&:hover {
		background: @white;
		border-color: @blue-200;
		color: @blue-700;
	}
}

/* ====== 右侧对话记录面板 ====== */
.history-panel {
	width: 280px;
	display: flex;
	flex-direction: column;
	background: @white;
	flex-shrink: 0;
}

.history-header {
	display: flex;
	align-items: center;
	gap: 10px;
	padding: 16px 20px;
	border-bottom: 1px solid @gray-100;

	.header-indicator {
		width: 4px;
		height: 16px;
		border-radius: 2px;
		background: linear-gradient(180deg, @blue-400, @blue-600);
	}
	.header-title {
		font-size: 15px;
		font-weight: 600;
		color: @gray-600;
	}
}

.history-list {
	flex: 1;
	overflow-y: auto;
	padding: 8px;

	&::-webkit-scrollbar {
		width: 4px;
	}
	&::-webkit-scrollbar-thumb {
		background: @gray-200;
		border-radius: 2px;
	}
}

.history-item {
	display: flex;
	align-items: center;
	gap: 10px;
	padding: 12px;
	border-radius: 10px;
	cursor: pointer;
	transition: all 0.2s;
	margin-bottom: 2px;

	&:hover {
		background: @blue-50;
	}
	&--active {
		background: @blue-50;
		border: 1px solid @blue-100;

		.history-item__title {
			color: @blue-700;
		}
		.history-item__icon {
			color: @blue-500;
		}
	}

	&__icon {
		color: @gray-400;
		flex-shrink: 0;
	}
	&__info {
		flex: 1;
		min-width: 0;
	}
	&__title {
		font-size: 13px;
		font-weight: 500;
		color: @gray-600;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	&__time {
		font-size: 11px;
		color: @gray-400;
		margin-top: 3px;
	}
	&__actions {
		display: flex;
		align-items: center;
		gap: 6px;
		flex-shrink: 0;
	}
	&__count {
		font-size: 11px;
		color: @gray-400;
		background: @gray-100;
		padding: 1px 8px;
		border-radius: 10px;
	}
	&__delete {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		border-radius: 6px;
		color: @gray-400;
		cursor: pointer;
		opacity: 0;
		transition: all 0.2s;
		&:hover {
			background: #fef0f0;
			color: #f56c6c;
		}
	}
	&:hover &__delete {
		opacity: 1;
	}
}

.history-footer {
	padding: 12px 16px;
	border-top: 1px solid @gray-100;

	.new-chat-btn {
		width: 100%;
		border-radius: 10px;
		font-size: 13px;
		font-weight: 500;
		border-color: @blue-200;
		color: @blue-600;
		&:hover {
			background: @blue-50;
			border-color: @blue-400;
		}
	}
}
</style>
