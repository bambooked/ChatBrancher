<script lang="ts">
	import { onMount } from 'svelte';
	import { apiClient } from '$lib/api';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import type { ChatResponse } from '$lib/types/api';
	import { API_BASE_URL } from '$lib/config';

	let chats = $state<ChatResponse[]>([]);
	let error = $state('');
	let loading = $state(true);

	onMount(async () => {
		if (!browser) return;

		const token = localStorage.getItem('access_token');
		if (!token) {
			await goto('/login');
			return;
		}

		try {
			chats = await apiClient.getChats(token);
		} catch (e) {
			error = 'チャット一覧の取得に失敗しました。エラーが発生しました。';
		} finally {
			loading = false;
		}
	});

	async function createNewChat() {
		if (!browser) return;

		const token = localStorage.getItem('access_token');
		if (!token) {
			await goto('/login');
			return;
		}

		try {
			const response = await fetch(`${API_BASE_URL}/api/v1/chats`, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${token}`
				}
			});

			if (response.ok) {
				const newChat: ChatResponse = await response.json();
				chats = [...chats, newChat];
				await goto(`/chats/${newChat.uuid}`);
			}
		} catch (e) {
			error = 'チャットの作成に失敗しました。';
		}
	}

	function selectChat(chatUuid: string) {
		goto(`/chats/${chatUuid}`);
	}
</script>

<div class="chats-container">
	<header>
		<h1>チャット一覧</h1>
		<button onclick={createNewChat}>新規チャット作成</button>
	</header>

	{#if loading}
		<p>読み込み中...</p>
	{:else if error}
		<div class="error">{error}</div>
	{:else if chats.length === 0}
		<p>チャットがありません。新規チャットを作成してください。</p>
	{:else}
		<ul class="chat-list">
			{#each chats as chat}
				<li>
					<button class="chat-item" onclick={() => selectChat(chat.uuid)}>
						<div class="chat-uuid">{chat.uuid}</div>
						<div class="chat-date">作成: {new Date(chat.created).toLocaleString('ja-JP')}</div>
					</button>
				</li>
			{/each}
		</ul>
	{/if}
</div>

<style>
	.chats-container {
		max-width: 800px;
		margin: 20px auto;
		padding: 20px;
	}

	header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;
	}

	h1 {
		margin: 0;
	}

	button {
		padding: 10px 20px;
		background-color: #007bff;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 14px;
	}

	button:hover {
		background-color: #0056b3;
	}

	.chat-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.chat-list li {
		margin-bottom: 10px;
	}

	.chat-item {
		width: 100%;
		text-align: left;
		padding: 15px;
		background-color: #f8f9fa;
		border: 1px solid #dee2e6;
		border-radius: 4px;
	}

	.chat-item:hover {
		background-color: #e9ecef;
	}

	.chat-uuid {
		font-weight: bold;
		margin-bottom: 5px;
		color: #495057;
	}

	.chat-date {
		font-size: 12px;
		color: #6c757d;
	}

	.error {
		color: red;
		padding: 10px;
		background-color: #fee;
		border-radius: 4px;
	}
</style>
