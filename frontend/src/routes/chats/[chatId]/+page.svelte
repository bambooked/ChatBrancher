<script lang="ts">
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import ChatTree from '$lib/components/ChatTree.svelte';
	import { ApiClient } from '$lib/api/client';
	import { buildTreeFromMessages } from '$lib/utils/tree';
	import type {
		ChatResponse,
		ChatTreeResponse,
		MessageResponse,
		TreeNode
	} from '$lib/types/api';

	interface Props {
		data: {
			chatId: string;
		};
	}

	const apiBase = 'http://localhost:8000';
	const apiClient = new ApiClient(apiBase);

	let { data }: Props = $props();

	let chats = $state<ChatResponse[]>([]);
	let chatTree = $state<ChatTreeResponse | null>(null);
	let tree = $state<TreeNode | null>(null);
	let messageMap = $state<Map<string, MessageResponse>>(new Map());
	let activePath = $state<string[]>([]);
	let activeNodeUuid = $state<string | null>(null);
	let loading = $state(true);
	let error = $state('');
	let sendingMessage = $state(false);
	let messageContent = $state('');
	let leftPanelVisible = $state(true);
	let rightPanelVisible = $state(true);
	let leftPanelWidth = $state(280);
	let rightPanelWidth = $state(320);
	let resizingPanel = $state<'left' | 'right' | null>(null);
	let resizeStartX = 0;
	let resizeStartWidth = 0;

	let chatsLoaded = false;
	let activeChatRequestId = 0;

	const MIN_LEFT_WIDTH = 220;
	const MAX_LEFT_WIDTH = 420;
	const MIN_RIGHT_WIDTH = 240;
	const MAX_RIGHT_WIDTH = 520;

	async function loadChats() {
		const token = localStorage.getItem('access_token');
		if (!token) {
			await goto('/login');
			loading = false;
			return;
		}

		try {
			chats = await apiClient.getChats(token);
		} catch (err) {
			error = 'チャット一覧の取得に失敗しました。';
			chatsLoaded = false;
		}
	}

	async function loadChatTree(chatId: string) {
		const requestId = ++activeChatRequestId;
		error = '';
		loading = true;
		messageContent = '';
		activePath = [];
		activeNodeUuid = null;
		messageMap = new Map();
		chatTree = null;
		tree = null;

		const token = localStorage.getItem('access_token');
		if (!token) {
			await goto('/login');
			return;
		}

		try {
			const fetchedChatTree = await apiClient.getChatTree(chatId, token);
			if (requestId !== activeChatRequestId) return;

			chatTree = fetchedChatTree;
			tree = buildTreeFromMessages(fetchedChatTree.messages);
			messageMap = new Map(fetchedChatTree.messages.map((msg) => [msg.uuid, msg]));

			const nextActiveUuid = selectLatestMessage(fetchedChatTree.messages);
			const path = nextActiveUuid ? findPath(tree, nextActiveUuid) : deriveDefaultPath(tree);

			activePath = path;
			activeNodeUuid = path[path.length - 1] ?? null;
		} catch (err) {
			error = 'チャットの取得に失敗しました。';
		} finally {
			if (requestId === activeChatRequestId) {
				loading = false;
			}
		}
	}

	function deriveDefaultPath(root: TreeNode | null) {
		if (!root) return [];
		const path = [root.uuid];
		let current = root;

		while (current.children.length > 0) {
			// pick the latest child by created_at
			const latestChild = [...current.children].sort((a, b) =>
				new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
			)[0];
			if (!latestChild) break;
			path.push(latestChild.uuid);
			current = latestChild;
		}

		return path;
	}

	function selectLatestMessage(messages: MessageResponse[]) {
		if (messages.length === 0) return null;
		return [...messages].sort(
			(a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
		)[0].uuid;
	}

	function findPath(root: TreeNode | null, targetUuid: string): string[] {
		if (!root) return [];

		const path: string[] = [];

		function dfs(node: TreeNode, current: string[]): boolean {
			const next = [...current, node.uuid];
			if (node.uuid === targetUuid) {
				path.push(...next);
				return true;
			}
			for (const child of node.children) {
				if (dfs(child, next)) return true;
			}
			return false;
		}

		dfs(root, []);
		return path;
	}

	function handleNodeSelect(nodeUuid: string) {
		if (!tree) return;
		const path = findPath(tree, nodeUuid);
		if (path.length === 0) return;
		activePath = path;
		activeNodeUuid = nodeUuid;
	}

	function handleConversationSelect(nodeUuid: string) {
		handleNodeSelect(nodeUuid);
	}

	function getConversationMessages() {
		return activePath
			.map((uuid) => messageMap.get(uuid))
			.filter((msg): msg is MessageResponse => Boolean(msg));
	}

	async function handleSendMessage(event: Event) {
		event.preventDefault();
		if (!messageContent.trim() || sendingMessage) return;
		const token = localStorage.getItem('access_token');
		if (!token) {
			await goto('/login');
			return;
		}

		try {
			sendingMessage = true;
			error = '';

			const parentUuid =
				activeNodeUuid ?? (activePath.length ? activePath[activePath.length - 1] : null);

			await apiClient.sendMessage(
				data.chatId,
				{
					content: messageContent,
					parent_message_uuid: parentUuid,
					llm_model: 'anthropic/claude-3-haiku'
				},
				token
			);

			messageContent = '';
			await loadChatTree(data.chatId);
		} catch (err) {
			error = 'メッセージの送信に失敗しました。';
		} finally {
			sendingMessage = false;
		}
	}

	async function createNewChat() {
		const token = localStorage.getItem('access_token');
		if (!token) {
			await goto('/login');
			return;
		}

		try {
			const response = await fetch(`${apiBase}/api/v1/chats`, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${token}`
				}
			});

			if (!response.ok) {
				throw new Error('Failed to create chat');
			}

			const newChat: ChatResponse = await response.json();
			chats = [...chats, newChat];
			await goto(`/chats/${newChat.uuid}`);
		} catch (err) {
			error = '新規チャットの作成に失敗しました。';
		}
	}

	function selectChat(chatUuid: string) {
		if (chatUuid === data.chatId) return;
		goto(`/chats/${chatUuid}`);
	}

	function toggleLeftPanel() {
		leftPanelVisible = !leftPanelVisible;
	}

	function toggleRightPanel() {
		rightPanelVisible = !rightPanelVisible;
	}

	function startResize(panel: 'left' | 'right', event: PointerEvent) {
		resizingPanel = panel;
		resizeStartX = event.clientX;
		resizeStartWidth = panel === 'left' ? leftPanelWidth : rightPanelWidth;
		const handleElement = event.currentTarget as HTMLElement | null;
		handleElement?.setPointerCapture(event.pointerId);
	}

	function handlePointerMove(event: PointerEvent) {
		if (!resizingPanel) return;
		const delta = event.clientX - resizeStartX;

		if (resizingPanel === 'left') {
			leftPanelWidth = clamp(resizeStartWidth + delta, MIN_LEFT_WIDTH, MAX_LEFT_WIDTH);
		}

		if (resizingPanel === 'right') {
			rightPanelWidth = clamp(resizeStartWidth - delta, MIN_RIGHT_WIDTH, MAX_RIGHT_WIDTH);
		}
	}

	function stopResize(event: PointerEvent) {
		if (resizingPanel) {
			const handleElement = event.currentTarget as HTMLElement | null;
			handleElement?.releasePointerCapture(event.pointerId);
		}
		resizingPanel = null;
	}

	function clamp(value: number, min: number, max: number) {
		return Math.min(Math.max(value, min), max);
	}

	const conversationMessages = $derived(getConversationMessages());
	const currentChat = $derived(chats.find((chat) => chat.uuid === data.chatId) ?? null);

	$effect(() => {
		if (!browser) return;

		const chatId = data.chatId;
		if (!chatId) return;

		if (!chatsLoaded) {
			chatsLoaded = true;
			loadChats();
		}

		loadChatTree(chatId);
	});
</script>

<div class="layout">
	<header class="page-header">
		<button class="back-link" onclick={() => goto('/chats')}>← 一覧</button>
		<div class="title-block">
			<h1>チャット画面</h1>
			{#if currentChat}
				<div class="subtitle">
					<span>チャットID: {currentChat.uuid}</span>
					<span>作成: {new Date(currentChat.created).toLocaleString('ja-JP')}</span>
				</div>
			{/if}
		</div>
	</header>

	{#if loading}
		<div class="loading-state">読み込み中...</div>
	{:else}
		<div class="workspace">
			{#if leftPanelVisible}
				<section
					class="side-panel left"
					style={`width: ${leftPanelWidth}px`}
				>
					<header class="panel-header">
						<h2>チャット管理</h2>
						<button class="panel-toggle" onclick={toggleLeftPanel} aria-label="左パネルを閉じる">
							×
						</button>
					</header>

					<button class="primary-button new-chat" onclick={createNewChat}>新規チャット</button>

					<ul class="chat-list">
						{#each chats as chat}
							<li>
								<button
									class:active={chat.uuid === data.chatId}
									onclick={() => selectChat(chat.uuid)}
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

				<div
					class="resize-handle left"
					onpointerdown={(event) => startResize('left', event)}
					onpointermove={handlePointerMove}
					onpointerup={stopResize}
					onpointercancel={stopResize}
				></div>
			{:else}
				<div class="collapsed-bar left">
					<button onclick={toggleLeftPanel} aria-label="左パネルを開く">▶</button>
				</div>
			{/if}

			<main class="conversation-area">
				<div class="conversation-toolbar">
					<div class="toolbar-group">
						<button onclick={toggleLeftPanel} class:active={leftPanelVisible}>
							{leftPanelVisible ? '⟵ 収納' : '⟶ 展開'}
						</button>
						<button onclick={toggleRightPanel} class:active={rightPanelVisible}>
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
					{#if conversationMessages.length === 0}
						<div class="empty-state">まだメッセージがありません。</div>
					{:else}
						<ul>
							{#each conversationMessages as message}
								<li>
									<button
										type="button"
										class="message-card"
										class:active={message.uuid === activeNodeUuid}
										onclick={() => handleConversationSelect(message.uuid)}
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
							<button type="submit" class="primary-button" disabled={sendingMessage || !messageContent.trim()}>
								{sendingMessage ? '送信中...' : '送信'}
							</button>
						</div>
					</form>
				</section>
			</main>

			{#if rightPanelVisible}
				<div
					class="resize-handle right"
					onpointerdown={(event) => startResize('right', event)}
					onpointermove={handlePointerMove}
					onpointerup={stopResize}
					onpointercancel={stopResize}
				></div>

				<section
					class="side-panel right"
					style={`width: ${rightPanelWidth}px`}
				>
					<header class="panel-header">
						<h2>ツリーの探索</h2>
						<button class="panel-toggle" onclick={toggleRightPanel} aria-label="右パネルを閉じる">
							×
						</button>
					</header>

					{#if tree}
						<ChatTree
							tree={tree}
							onNodeSelect={handleNodeSelect}
							activeNodeUuid={activeNodeUuid}
						/>
					{:else}
						<div class="empty-state tree">ツリーがありません。</div>
					{/if}
				</section>
			{:else}
				<div class="collapsed-bar right">
					<button onclick={toggleRightPanel} aria-label="右パネルを開く">◀</button>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	:global(body) {
		background: #f5f6fa;
	}

	.layout {
		display: flex;
		flex-direction: column;
		height: 100vh;
		overflow: hidden;
		color: #1f2933;
	}

	.page-header {
		display: flex;
		align-items: center;
		gap: 16px;
		padding: 16px 24px;
		background: #ffffff;
		border-bottom: 1px solid #e2e8f0;
	}

	.back-link {
		background: transparent;
		border: none;
		color: #2563eb;
		cursor: pointer;
		font-size: 14px;
		padding: 8px;
	}

	.title-block h1 {
		margin: 0;
		font-size: 20px;
		font-weight: 600;
	}

	.subtitle {
		font-size: 12px;
		color: #64748b;
		display: flex;
		gap: 12px;
		margin-top: 4px;
	}

	.loading-state {
		padding: 32px;
		text-align: center;
		color: #64748b;
	}

	.workspace {
		display: flex;
		flex: 1;
		min-height: 0;
	}

	.side-panel {
		display: flex;
		flex-direction: column;
		padding: 20px;
		background: #ffffff;
		border-right: 1px solid #e2e8f0;
		overflow: hidden auto;
	}

	.side-panel.right {
		border-right: none;
		border-left: 1px solid #e2e8f0;
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

	.resize-handle {
		width: 6px;
		cursor: col-resize;
		background: linear-gradient(180deg, rgba(148, 163, 184, 0.2), rgba(148, 163, 184, 0.05));
	}

	.resize-handle.left {
		border-right: 1px solid #e2e8f0;
	}

	.resize-handle.right {
		border-left: 1px solid #e2e8f0;
	}

	.collapsed-bar {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		background: #ffffff;
		border-right: 1px solid #e2e8f0;
	}

	.collapsed-bar.right {
		border-right: none;
		border-left: 1px solid #e2e8f0;
	}

	.collapsed-bar button {
		border: none;
		background: transparent;
		cursor: pointer;
		color: #2563eb;
		font-size: 16px;
	}

	.empty-state {
		padding: 32px;
		text-align: center;
		color: #94a3b8;
		background: #ffffff;
		border-radius: 8px;
		border: 1px dashed #cbd5e1;
	}

	.empty-state.tree {
		background: transparent;
		border: none;
	}

	@media (max-width: 960px) {
		.workspace {
			flex-direction: column;
		}

		.side-panel {
			width: 100% !important;
			border-right: none;
			border-left: none;
			border-bottom: 1px solid #e2e8f0;
			flex: unset;
		}

		.resize-handle,
		.collapsed-bar {
			display: none;
		}
	}
</style>
