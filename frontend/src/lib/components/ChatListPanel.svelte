<script lang="ts">
	import type { ChatResponse } from '$lib/types/api';

	interface Props {
		chats: ChatResponse[];
		currentChatId: string;
		visible: boolean;
		width: number;
		onChatSelect?: (chatId: string) => void;
		onNewChat?: () => void;
		onToggle?: () => void;
	}

	let { chats, currentChatId, visible, width, onChatSelect, onNewChat, onToggle }: Props = $props();

	function handleChatSelect(chatId: string) {
		if (onChatSelect) {
			onChatSelect(chatId);
		}
	}

	function handleNewChat() {
		if (onNewChat) {
			onNewChat();
		}
	}

	function handleToggle() {
		if (onToggle) {
			onToggle();
		}
	}
</script>

{#if visible}
	<section class="side-panel" style={`width: ${width}px`}>
		<header class="panel-header">
			<h2>チャット管理</h2>
			<button class="panel-toggle" onclick={handleToggle} aria-label="左パネルを閉じる">
				×
			</button>
		</header>

		<button class="primary-button new-chat" onclick={handleNewChat}>新規チャット</button>

		<ul class="chat-list">
			{#each chats as chat}
				<li>
					<button
						class:active={chat.uuid === currentChatId}
						onclick={() => handleChatSelect(chat.uuid)}
					>
						<div class="chat-title">{chat.uuid}</div>
						<div class="chat-meta">
							{new Date(chat.created).toLocaleDateString('ja-JP')}
						</div>
					</button>
				</li>
			{/each}
		</ul>
	</section>
{:else}
	<div class="collapsed-bar">
		<button onclick={handleToggle} aria-label="左パネルを開く">▶</button>
	</div>
{/if}

<style>
	.side-panel {
		display: flex;
		flex-direction: column;
		padding: 20px;
		background: #ffffff;
		border-right: 1px solid #e2e8f0;
		overflow: hidden auto;
	}

	.panel-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 16px;
	}

	.panel-header h2 {
		margin: 0;
		font-size: 16px;
		font-weight: 600;
	}

	.panel-toggle {
		border: none;
		background: transparent;
		font-size: 18px;
		line-height: 1;
		cursor: pointer;
		color: #94a3b8;
	}

	.primary-button {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 10px 16px;
		background: #2563eb;
		color: #ffffff;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 14px;
		gap: 8px;
	}

	.primary-button:disabled {
		background: #94a3b8;
		cursor: not-allowed;
	}

	.new-chat {
		width: 100%;
		margin-bottom: 20px;
	}

	.chat-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.chat-list li button {
		width: 100%;
		text-align: left;
		padding: 12px;
		border-radius: 8px;
		border: 1px solid #e2e8f0;
		background: #ffffff;
		cursor: pointer;
		font-size: 13px;
		display: flex;
		flex-direction: column;
		gap: 4px;
		transition: border-color 0.2s ease, box-shadow 0.2s ease;
	}

	.chat-list li button:hover {
		border-color: #2563eb;
		box-shadow: 0 2px 6px rgba(37, 99, 235, 0.12);
	}

	.chat-list li button.active {
		background: #eff6ff;
		border-color: #2563eb;
	}

	.chat-title {
		font-weight: 600;
		word-break: break-all;
	}

	.chat-meta {
		color: #64748b;
		font-size: 12px;
	}

	.collapsed-bar {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		background: #ffffff;
		border-right: 1px solid #e2e8f0;
	}

	.collapsed-bar button {
		border: none;
		background: transparent;
		cursor: pointer;
		color: #2563eb;
		font-size: 16px;
	}
</style>
