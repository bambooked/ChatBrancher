<script lang="ts">
	import { ApiClient } from '$lib/api/client';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';

	let username = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	const apiClient = new ApiClient('http://localhost:8000');

	async function handleSubmit(event: Event) {
		event.preventDefault();
		error = '';
		loading = true;

		try {
			const response = await apiClient.login({ username, password });

			if (browser) {
				localStorage.setItem('access_token', response.access_token);
				await goto('/chats');
			}
		} catch (e) {
			error = 'ログインに失敗しました。ユーザー名またはパスワードを確認してください。';
		} finally {
			loading = false;
		}
	}
</script>

<div class="login-container">
	<h1>ログイン</h1>
	<form onsubmit={handleSubmit}>
		<div class="form-group">
			<label for="username">Username</label>
			<input
				id="username"
				type="text"
				bind:value={username}
				disabled={loading}
				required
			/>
		</div>
		<div class="form-group">
			<label for="password">Password</label>
			<input
				id="password"
				type="password"
				bind:value={password}
				disabled={loading}
				required
			/>
		</div>
		{#if error}
			<div class="error">{error}</div>
		{/if}
		<button type="submit" disabled={loading}>
			{loading ? 'ログイン中...' : 'Login'}
		</button>
	</form>
</div>

<style>
	.login-container {
		max-width: 400px;
		margin: 100px auto;
		padding: 20px;
		border: 1px solid #ccc;
		border-radius: 8px;
	}

	h1 {
		text-align: center;
		margin-bottom: 20px;
	}

	.form-group {
		margin-bottom: 15px;
	}

	label {
		display: block;
		margin-bottom: 5px;
		font-weight: bold;
	}

	input {
		width: 100%;
		padding: 8px;
		border: 1px solid #ddd;
		border-radius: 4px;
		box-sizing: border-box;
	}

	button {
		width: 100%;
		padding: 10px;
		background-color: #007bff;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 16px;
	}

	button:hover:not(:disabled) {
		background-color: #0056b3;
	}

	button:disabled {
		background-color: #ccc;
		cursor: not-allowed;
	}

	.error {
		color: red;
		margin-bottom: 10px;
		padding: 10px;
		background-color: #fee;
		border-radius: 4px;
	}
</style>
