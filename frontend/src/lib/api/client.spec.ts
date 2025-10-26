import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ApiClient } from './client';
import type {
	LoginRequest,
	TokenResponse,
	ChatResponse,
	ChatTreeResponse,
	SendMessageRequest,
	SendMessageResponse
} from '$lib/types/api';

describe('ApiClient', () => {
	let client: ApiClient;
	const baseUrl = 'http://localhost:8000';

	beforeEach(() => {
		client = new ApiClient(baseUrl);
		vi.resetAllMocks();
	});

	describe('login', () => {
		it('should send POST request to /api/v1/auth/login with credentials', async () => {
			const mockResponse: TokenResponse = {
				access_token: 'test-token-123',
				token_type: 'bearer'
			};

			const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue({
				ok: true,
				json: async () => mockResponse
			} as Response);

			const request: LoginRequest = {
				username: 'testuser',
				password: 'testpass'
			};

			const result = await client.login(request);

			expect(fetchSpy).toHaveBeenCalledWith(`${baseUrl}/api/v1/auth/login`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(request)
			});
			expect(result).toEqual(mockResponse);
		});

		it('should throw error when login fails', async () => {
			vi.spyOn(global, 'fetch').mockResolvedValue({
				ok: false,
				status: 401,
				json: async () => ({ detail: 'Incorrect username or password' })
			} as Response);

			const request: LoginRequest = {
				username: 'wronguser',
				password: 'wrongpass'
			};

			await expect(client.login(request)).rejects.toThrow();
		});
	});

	describe('getChats', () => {
		it('should send GET request to /api/v1/chats with auth token', async () => {
			const mockChats: ChatResponse[] = [
				{
					uuid: 'chat-1',
					owner_uuid: 'user-1',
					created: '2024-01-01T00:00:00',
					updated: '2024-01-01T00:00:00'
				}
			];

			const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue({
				ok: true,
				json: async () => mockChats
			} as Response);

			const token = 'test-token';
			const result = await client.getChats(token);

			expect(fetchSpy).toHaveBeenCalledWith(`${baseUrl}/api/v1/chats`, {
				method: 'GET',
				headers: {
					Authorization: `Bearer ${token}`
				}
			});
			expect(result).toEqual(mockChats);
		});

		it('should throw error when unauthorized', async () => {
			vi.spyOn(global, 'fetch').mockResolvedValue({
				ok: false,
				status: 401
			} as Response);

			await expect(client.getChats('invalid-token')).rejects.toThrow();
		});
	});

	describe('getChatTree', () => {
		it('should send GET request to /api/v1/chats/{uuid} with auth token', async () => {
			const chatUuid = 'chat-123';
			const mockChatTree: ChatTreeResponse = {
				uuid: chatUuid,
				owner_uuid: 'user-1',
				created: '2024-01-01T00:00:00',
				updated: '2024-01-01T00:00:00',
				messages: [
					{
						uuid: 'msg-1',
						role: 'user',
						content: 'Hello',
						parent_uuid: null,
						created_at: '2024-01-01T00:00:00',
						updated_at: '2024-01-01T00:00:00'
					}
				]
			};

			const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue({
				ok: true,
				json: async () => mockChatTree
			} as Response);

			const token = 'test-token';
			const result = await client.getChatTree(chatUuid, token);

			expect(fetchSpy).toHaveBeenCalledWith(`${baseUrl}/api/v1/chats/${chatUuid}`, {
				method: 'GET',
				headers: {
					Authorization: `Bearer ${token}`
				}
			});
			expect(result).toEqual(mockChatTree);
		});

		it('should throw error when chat not found', async () => {
			vi.spyOn(global, 'fetch').mockResolvedValue({
				ok: false,
				status: 404
			} as Response);

			await expect(client.getChatTree('non-existent', 'token')).rejects.toThrow();
		});
	});

	describe('sendMessage', () => {
		it('should send POST request to /api/v1/chats/{uuid}/messages', async () => {
			const chatUuid = 'chat-123';
			const request: SendMessageRequest = {
				content: 'Hello, how are you?',
				parent_message_uuid: null,
				llm_model: 'anthropic/claude-3-haiku'
			};

			const mockResponse: SendMessageResponse = {
				user_message: {
					uuid: 'msg-user-1',
					role: 'user',
					content: 'Hello, how are you?',
					parent_uuid: null,
					created_at: '2024-01-01T00:00:00',
					updated_at: '2024-01-01T00:00:00'
				},
				assistant_message: {
					uuid: 'msg-assistant-1',
					role: 'assistant',
					content: "I'm doing well, thank you!",
					parent_uuid: 'msg-user-1',
					created_at: '2024-01-01T00:00:01',
					updated_at: '2024-01-01T00:00:01'
				}
			};

			const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue({
				ok: true,
				json: async () => mockResponse
			} as Response);

			const token = 'test-token';
			const result = await client.sendMessage(chatUuid, request, token);

			expect(fetchSpy).toHaveBeenCalledWith(`${baseUrl}/api/v1/chats/${chatUuid}/messages`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${token}`
				},
				body: JSON.stringify(request)
			});
			expect(result).toEqual(mockResponse);
		});

		it('should throw error when sending message fails', async () => {
			vi.spyOn(global, 'fetch').mockResolvedValue({
				ok: false,
				status: 400
			} as Response);

			const request: SendMessageRequest = {
				content: 'Hello',
				parent_message_uuid: null
			};

			await expect(client.sendMessage('chat-123', request, 'token')).rejects.toThrow();
		});
	});
});
