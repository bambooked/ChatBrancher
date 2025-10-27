<script lang="ts">
	import type { MessageResponse } from '$lib/types/api';

	interface Props {
		messages: MessageResponse[];
		activeNodeUuid: string | null;
		sendingMessage: boolean;
		error: string;
		leftPanelVisible: boolean;
		rightPanelVisible: boolean;
		onNodeSelect?: (nodeUuid: string) => void;
		onSendMessage?: (content: string) => void;
		onToggleLeftPanel?: () => void;
		onToggleRightPanel?: () => void;
	}

	let {
		messages,
		activeNodeUuid,
		sendingMessage,
		error,
		leftPanelVisible,
		rightPanelVisible,
		onNodeSelect,
		onSendMessage,
		onToggleLeftPanel,
		onToggleRightPanel
	}: Props = $props();

	let messageContent = $state('');

	function handleNodeSelect(nodeUuid: string) {
		if (onNodeSelect) {
			onNodeSelect(nodeUuid);
		}
	}

	function handleSendMessage(event: Event) {
		event.preventDefault();
		if (!messageContent.trim() || sendingMessage) return;
		if (onSendMessage) {
			onSendMessage(messageContent);
			messageContent = '';
		}
	}

	function handleToggleLeftPanel() {
		if (onToggleLeftPanel) {
			onToggleLeftPanel();
		}
	}

	function handleToggleRightPanel() {
		if (onToggleRightPanel) {
			onToggleRightPanel();
		}
	}
</script>

<main class="conversation-area">
	<div class="conversation-toolbar">
		<div class="toolbar-group">
			<button onclick={handleToggleLeftPanel} class:active={leftPanelVisible}>
				{leftPanelVisible ? '⟵ 収納' : '⟶ 展開'}
			</button>
			<button onclick={handleToggleRightPanel} class:active={rightPanelVisible}>
				{rightPanelVisible ? '収納 ⟶' : '展開 ⟵'}
			</button>
		</div>
		{#if activeNodeUuid}
			<div class="toolbar-status">選択中: {activeNodeUuid}</div>
		{/if}
	</div>

	{#if error && !sendingMessage}
		<div class="alert-error">{error}</div>
	{/if}

	<section class="messages">
		{#if messages.length === 0}
			<div class="empty-state">まだメッセージがありません。</div>
		{:else}
			<ul>
				{#each messages as message}
					<li>
						<button
							type="button"
							class="message-card"
							class:active={message.uuid === activeNodeUuid}
							onclick={() => handleNodeSelect(message.uuid)}
						>
							<span class="message-header">
								<span class="role {message.role}">
									{message.role === 'assistant' ? 'アシスタント' : 'ユーザー'}
								</span>
								<time>
									{new Date(message.created_at).toLocaleString('ja-JP')}
								</time>
							</span>
							<span class="message-body">{message.content}</span>
						</button>
					</li>
				{/each}
			</ul>
		{/if}
	</section>

	<section class="composer">
		<form onsubmit={handleSendMessage}>
			<textarea
				bind:value={messageContent}
				placeholder="メッセージを入力..."
				rows="4"
				disabled={sendingMessage}
			></textarea>
			<div class="composer-footer">
				{#if error}
					<div class="error-inline">{error}</div>
				{/if}
				<button
					type="submit"
					class="primary-button"
					disabled={sendingMessage || !messageContent.trim()}
				>
					{sendingMessage ? '送信中...' : '送信'}
				</button>
			</div>
		</form>
	</section>
</main>

<style>
	.conversation-area {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-width: 0;
		padding: 24px;
		overflow: hidden;
	}

	.conversation-toolbar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 16px;
	}

	.toolbar-group {
		display: flex;
		gap: 8px;
	}

	.toolbar-group button {
		border: 1px solid #cbd5e1;
		border-radius: 6px;
		background: #ffffff;
		cursor: pointer;
		padding: 6px 12px;
		font-size: 12px;
		color: #475569;
	}

	.toolbar-group button.active {
		border-color: #2563eb;
		color: #2563eb;
	}

	.toolbar-status {
		font-size: 12px;
		color: #64748b;
	}

	.alert-error {
		padding: 12px;
		background: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 6px;
		color: #dc2626;
		font-size: 14px;
		margin-bottom: 16px;
	}

	.messages {
		flex: 1;
		overflow: hidden auto;
		padding-right: 4px;
	}

	.messages ul {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.message-card {
		padding: 14px 16px;
		background: #ffffff;
		border-radius: 10px;
		border: 1px solid #e2e8f0;
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
		cursor: pointer;
		display: flex;
		flex-direction: column;
		gap: 8px;
		width: 100%;
		text-align: left;
		color: inherit;
		font: inherit;
	}

	.message-card.active {
		border-color: #2563eb;
		box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.15);
	}

	.message-card:focus-visible {
		outline: 2px solid rgba(37, 99, 235, 0.35);
		outline-offset: 2px;
	}

	.message-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		font-size: 12px;
		color: #64748b;
	}

	.message-body {
		margin: 0;
		font-size: 14px;
		line-height: 1.6;
		white-space: pre-wrap;
		word-break: break-word;
		color: #1f2937;
	}

	.role {
		font-weight: 600;
	}

	.role.user {
		color: #2563eb;
	}

	.role.assistant {
		color: #10b981;
	}

	.composer {
		padding-top: 16px;
		margin-top: 16px;
		border-top: 1px solid #e2e8f0;
	}

	.composer form {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.composer textarea {
		width: 100%;
		border-radius: 8px;
		border: 1px solid #cbd5e1;
		padding: 12px;
		font: inherit;
		resize: vertical;
		min-height: 120px;
	}

	.composer textarea:focus {
		outline: none;
		border-color: #2563eb;
		box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.2);
	}

	.composer textarea:disabled {
		background: #f8fafc;
		cursor: not-allowed;
	}

	.composer-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 12px;
	}

	.error-inline {
		color: #dc2626;
		font-size: 13px;
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

	.empty-state {
		padding: 32px;
		text-align: center;
		color: #94a3b8;
		background: #ffffff;
		border-radius: 8px;
		border: 1px dashed #cbd5e1;
	}
</style>
