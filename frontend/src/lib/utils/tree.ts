import type { MessageResponse, TreeNode } from '$lib/types/api';

/**
 * parent_uuid形式のメッセージ配列をchildren形式のツリーに変換する
 */
export function buildTreeFromMessages(messages: MessageResponse[]): TreeNode | null {
	if (messages.length === 0) {
		return null;
	}

	// ルートノードを見つける
	const rootMessage = messages.find((msg) => msg.parent_uuid === null);
	if (!rootMessage) {
		return null;
	}

	// メッセージをUUIDでマップ化
	const messageMap = new Map<string, TreeNode>();
	messages.forEach((msg) => {
		messageMap.set(msg.uuid, { ...msg, children: [] });
	});

	// 親子関係を構築
	messages.forEach((msg) => {
		if (msg.parent_uuid) {
			const parent = messageMap.get(msg.parent_uuid);
			const child = messageMap.get(msg.uuid);
			if (parent && child) {
				parent.children.push(child);
			}
		}
	});

	return messageMap.get(rootMessage.uuid) || null;
}
