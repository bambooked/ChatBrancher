<script lang="ts">
	import { onMount } from 'svelte';
	import { ApiClient } from '$lib/api/client';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { buildTreeFromMessages } from '$lib/utils/tree';
	import ChatTree from '$lib/components/ChatTree.svelte';
	import type { ChatTreeResponse, TreeNode } from '$lib/types/api';

	interface Props {
		data: {
			chatId: string;
		};
	}

	let { data }: Props = $props();

	let chatTree = $state<ChatTreeResponse | null>(null);
	let tree = $state<TreeNode | null>(null);
	let selectedNodeUuid = $state<string | null>(null);
	let error = $state('');
	let loading = $state(true);
	let sendingMessage = $state(false);
	let messageContent = $state('');

	const apiClient = new ApiClient('http://localhost:8000');

	onMount(async () => {
		await loadChatTree();
	});

	async function loadChatTree() {
		if (!browser) return;

		const token = localStorage.getItem('access_token');
		if (!token) {
			await goto('/login');
			return;
		}

		try {
			loading = true;
			chatTree = await apiClient.getChatTree(data.chatId, token);
			tree = buildTreeFromMessages(chatTree.messages);
		} catch (e) {
			error = 'チャットの取得に失敗しました。エラーが発生しました。';
		} finally {
			loading = false;
		}
	}

	async function handleSendMessage(event: Event) {
		event.preventDefault();
		if (!messageContent.trim() || sendingMessage) return;

		if (!browser) return;

		const token = localStorage.getItem('access_token');
		if (!token) {
			await goto('/login');
			return;
		}

		try {
			sendingMessage = true;
			error = '';

			await apiClient.sendMessage(
				data.chatId,
				{
					content: messageContent,
					parent_message_uuid: selectedNodeUuid,
					llm_model: 'anthropic/claude-3-haiku'
				},
				token
			);

			// メッセージ送信後、チャットツリーを再読み込み
			await loadChatTree();
			messageContent = '';
		} catch (e) {
			error = 'メッセージの送信に失敗しました。';
		} finally {
			sendingMessage = false;
		}
	}

	function handleNodeSelect(nodeUuid: string) {
		selectedNodeUuid = nodeUuid;
	}
</script>

<div class="chat-detail-container">
	<header>
		<button onclick={() => goto('/chats')}>← チャット一覧に戻る</button>
		<h1>チャット詳細</h1>
	</header>

	{#if loading}
		<p>読み込み中...</p>
	{:else if error && !chatTree}
		<div class="error">{error}</div>
	{:else if chatTree}
		<div class="chat-info">
			<p>チャットID: {chatTree.uuid}</p>
			<p>作成日時: {new Date(chatTree.created).toLocaleString('ja-JP')}</p>
			{#if selectedNodeUuid}
				<p>選択中のノード: {selectedNodeUuid}</p>
			{/if}
		</div>

		<div class="tree-section">
			<h2>メッセージツリー</h2>
			<ChatTree {tree} onNodeSelect={handleNodeSelect} />
		</div>

		<div class="message-form-section">
			<h2>メッセージを送信</h2>
			{#if !selectedNodeUuid && tree}
				<p class="hint">
					ツリー内のノードをクリックして、そのメッセージへの返信として送信できます。
					<br />
					何も選択しない場合は、最後のメッセージへの返信として送信されます。
				</p>
			{/if}

			<form onsubmit={handleSendMessage}>
				<textarea
					bind:value={messageContent}
					placeholder="メッセージを入力..."
					disabled={sendingMessage}
					rows="4"
				></textarea>
				{#if error && chatTree}
					<div class="error">{error}</div>
				{/if}
				<button type="submit" disabled={sendingMessage || !messageContent.trim()}>
					{sendingMessage ? '送信中...' : '送信'}
				</button>
			</form>
		</div>
	{/if}
</div>

<style>
	.chat-detail-container {
		max-width: 1200px;
		margin: 20px auto;
		padding: 20px;
	}

	header {
		display: flex;
		align-items: center;
		gap: 20px;
		margin-bottom: 20px;
	}

	header button {
		padding: 8px 16px;
		background-color: #6c757d;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
	}

	header button:hover {
		background-color: #5a6268;
	}

	h1 {
		margin: 0;
		flex: 1;
	}

	h2 {
		margin-top: 30px;
		margin-bottom: 15px;
		font-size: 1.25rem;
	}

	.chat-info {
		background-color: #f8f9fa;
		padding: 15px;
		border-radius: 4px;
		margin-bottom: 20px;
	}

	.chat-info p {
		margin: 5px 0;
		font-size: 14px;
		color: #495057;
	}

	.tree-section {
		margin-bottom: 30px;
	}

	.message-form-section {
		background-color: #fff;
		padding: 20px;
		border: 1px solid #dee2e6;
		border-radius: 8px;
	}

	.hint {
		background-color: #e7f3ff;
		padding: 12px;
		border-radius: 4px;
		margin-bottom: 15px;
		font-size: 14px;
		color: #0c5460;
		line-height: 1.6;
	}

	form {
		display: flex;
		flex-direction: column;
		gap: 15px;
	}

	textarea {
		width: 100%;
		padding: 12px;
		border: 1px solid #ced4da;
		border-radius: 4px;
		font-family: inherit;
		font-size: 14px;
		resize: vertical;
		box-sizing: border-box;
	}

	textarea:focus {
		outline: none;
		border-color: #80bdff;
		box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
	}

	textarea:disabled {
		background-color: #e9ecef;
		cursor: not-allowed;
	}

	button[type='submit'] {
		align-self: flex-end;
		padding: 10px 30px;
		background-color: #007bff;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 16px;
	}

	button[type='submit']:hover:not(:disabled) {
		background-color: #0056b3;
	}

	button[type='submit']:disabled {
		background-color: #ccc;
		cursor: not-allowed;
	}

	.error {
		color: red;
		padding: 10px;
		background-color: #fee;
		border-radius: 4px;
		margin: 10px 0;
	}
</style>
