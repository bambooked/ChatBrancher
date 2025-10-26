import { describe, it, expect } from 'vitest';
import { buildTreeFromMessages } from './tree';
import type { MessageResponse } from '$lib/types/api';

describe('buildTreeFromMessages', () => {
	it('should convert parent_uuid format to children format', () => {
		const messages: MessageResponse[] = [
			{
				uuid: 'msg-1',
				role: 'user',
				content: 'Hello',
				parent_uuid: null,
				created_at: '2024-01-01T00:00:00',
				updated_at: '2024-01-01T00:00:00'
			},
			{
				uuid: 'msg-2',
				role: 'assistant',
				content: 'Hi!',
				parent_uuid: 'msg-1',
				created_at: '2024-01-01T00:00:01',
				updated_at: '2024-01-01T00:00:01'
			}
		];

		const tree = buildTreeFromMessages(messages);

		expect(tree).toEqual({
			uuid: 'msg-1',
			role: 'user',
			content: 'Hello',
			parent_uuid: null,
			created_at: '2024-01-01T00:00:00',
			updated_at: '2024-01-01T00:00:00',
			children: [
				{
					uuid: 'msg-2',
					role: 'assistant',
					content: 'Hi!',
					parent_uuid: 'msg-1',
					created_at: '2024-01-01T00:00:01',
					updated_at: '2024-01-01T00:00:01',
					children: []
				}
			]
		});
	});

	it('should handle multiple branches', () => {
		const messages: MessageResponse[] = [
			{
				uuid: 'msg-1',
				role: 'user',
				content: 'Root',
				parent_uuid: null,
				created_at: '2024-01-01T00:00:00',
				updated_at: '2024-01-01T00:00:00'
			},
			{
				uuid: 'msg-2',
				role: 'assistant',
				content: 'Response 1',
				parent_uuid: 'msg-1',
				created_at: '2024-01-01T00:00:01',
				updated_at: '2024-01-01T00:00:01'
			},
			{
				uuid: 'msg-3',
				role: 'assistant',
				content: 'Response 2',
				parent_uuid: 'msg-1',
				created_at: '2024-01-01T00:00:02',
				updated_at: '2024-01-01T00:00:02'
			}
		];

		const tree = buildTreeFromMessages(messages);

		expect(tree.children).toHaveLength(2);
		expect(tree.children[0].uuid).toBe('msg-2');
		expect(tree.children[1].uuid).toBe('msg-3');
	});

	it('should handle empty array', () => {
		const messages: MessageResponse[] = [];
		const tree = buildTreeFromMessages(messages);
		expect(tree).toBeNull();
	});

	it('should handle deep nesting', () => {
		const messages: MessageResponse[] = [
			{
				uuid: 'msg-1',
				role: 'user',
				content: 'Level 1',
				parent_uuid: null,
				created_at: '2024-01-01T00:00:00',
				updated_at: '2024-01-01T00:00:00'
			},
			{
				uuid: 'msg-2',
				role: 'assistant',
				content: 'Level 2',
				parent_uuid: 'msg-1',
				created_at: '2024-01-01T00:00:01',
				updated_at: '2024-01-01T00:00:01'
			},
			{
				uuid: 'msg-3',
				role: 'user',
				content: 'Level 3',
				parent_uuid: 'msg-2',
				created_at: '2024-01-01T00:00:02',
				updated_at: '2024-01-01T00:00:02'
			}
		];

		const tree = buildTreeFromMessages(messages);

		expect(tree?.children[0]?.children[0]?.uuid).toBe('msg-3');
	});
});
