import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import ChatDetailPage from './+page.svelte';
import type { ChatTreeResponse } from '$lib/types/api';

describe('Chat Detail Page', () => {
	beforeEach(() => {
		vi.resetAllMocks();
		const localStorageMock = (() => {
			let store: Record<string, string> = {};
			return {
				getItem: (key: string) => store[key] || null,
				setItem: (key: string, value: string) => {
					store[key] = value;
				},
				clear: () => {
					store = {};
				}
			};
		})();
		vi.stubGlobal('localStorage', localStorageMock);
		localStorage.setItem('access_token', 'test-token');
	});

	it('should display messages in a list', async () => {
		const mockChatTree: ChatTreeResponse = {
			uuid: 'chat-123',
			owner_uuid: 'user-1',
			created: '2024-01-01T00:00:00',
			updated: '2024-01-01T00:00:00',
			messages: [
				{
					uuid: 'msg-1',
					role: 'user',
					content: 'こんにちは',
					parent_uuid: null,
					created_at: '2024-01-01T00:00:00',
					updated_at: '2024-01-01T00:00:00'
				},
				{
					uuid: 'msg-2',
					role: 'assistant',
					content: 'こんにちは！何かお手伝いできることはありますか？',
					parent_uuid: 'msg-1',
					created_at: '2024-01-01T00:01:00',
					updated_at: '2024-01-01T00:01:00'
				}
			]
		};

		vi.spyOn(global, 'fetch').mockResolvedValue({
			ok: true,
			json: async () => mockChatTree
		} as Response);

		render(ChatDetailPage, { props: { data: { chatId: 'chat-123' } } });

		await waitFor(() => {
			expect(screen.getByText(/こんにちは/i)).toBeDefined();
			expect(screen.getByText(/何かお手伝いできることはありますか/i)).toBeDefined();
		});
	});

	it('should display error message when fetching chat fails', async () => {
		vi.spyOn(global, 'fetch').mockResolvedValue({
			ok: false,
			status: 404
		} as Response);

		render(ChatDetailPage, { props: { data: { chatId: 'non-existent' } } });

		await waitFor(() => {
			expect(screen.getByText(/エラー/i)).toBeDefined();
		});
	});
});
