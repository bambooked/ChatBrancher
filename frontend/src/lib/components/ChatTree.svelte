<script lang="ts">
	import type { TreeNode } from '$lib/types/api';

	interface Props {
		tree: TreeNode | null;
		onNodeSelect?: (nodeUuid: string) => void;
	}

	let { tree, onNodeSelect }: Props = $props();

	let selectedNode = $state<string | null>(null);
	let currentPath = $state<string[]>([]);

	// Configuration
	const nodeWidth = 180;
	const nodeHeight = 80;
	const horizontalSpacing = 240;
	const verticalSpacing = 120;

	// Calculate node positions
	function calculateLayout(node: TreeNode | null) {
		if (!node) return [];
		const nodes: Array<TreeNode & { x: number; y: number; level: number }> = [];

		function layoutNode(
			currentNode: TreeNode,
			level = 0,
			parentX = 0,
			siblingIndex = 0,
			siblingCount = 1
		) {
			const xOffset = (siblingIndex - (siblingCount - 1) / 2) * horizontalSpacing;
			const x = level === 0 ? 150 : parentX + xOffset;
			const y = 50 + level * verticalSpacing;

			const renderNode = {
				...currentNode,
				x,
				y,
				level
			};

			nodes.push(renderNode);

			if (currentNode.children.length > 0) {
				currentNode.children.forEach((child, index) => {
					layoutNode(child, level + 1, x, index, currentNode.children.length);
				});
			}
		}

		layoutNode(node);
		return nodes;
	}

	// Generate connections between nodes
	function generateConnections(
		renderNodes: Array<TreeNode & { x: number; y: number; level: number }>,
		pathUuids: string[]
	) {
		const connections: Array<{ from: string; to: string; path: string; isActive: boolean }> = [];

		function addConnections(node: TreeNode & { x: number; y: number; level: number }) {
			node.children.forEach((child) => {
				const childNode = renderNodes.find((n) => n.uuid === child.uuid);
				if (!childNode) return;

				const isActive = pathUuids.includes(node.uuid) && pathUuids.includes(child.uuid);
				const path = `M ${node.x + nodeWidth / 2} ${node.y + nodeHeight} L ${childNode.x + nodeWidth / 2} ${childNode.y}`;

				connections.push({
					from: node.uuid,
					to: child.uuid,
					path,
					isActive
				});

				addConnections(childNode);
			});
		}

		const rootNode = renderNodes.find((n) => n.level === 0);
		if (rootNode) {
			addConnections(rootNode);
		}

		return connections;
	}

	// Find path to a node
	function findPath(node: TreeNode | null, targetUuid: string): string[] {
		if (!node) return [];
		const path: string[] = [];

		function search(currentNode: TreeNode, currentPath: string[]): boolean {
			const newPath = [...currentPath, currentNode.uuid];
			if (currentNode.uuid === targetUuid) {
				path.push(...newPath);
				return true;
			}

			for (const child of currentNode.children) {
				if (search(child, newPath)) {
					return true;
				}
			}
			return false;
		}

		search(node, []);
		return path;
	}

	function handleNodeClick(nodeUuid: string) {
		selectedNode = nodeUuid;
		const path = findPath(tree, nodeUuid);
		currentPath = path;
		if (onNodeSelect) {
			onNodeSelect(nodeUuid);
		}
	}

	function truncateContent(content: string, maxLength = 100) {
		return content.length > maxLength ? content.slice(0, maxLength) + '...' : content;
	}

	let renderNodes = $derived(calculateLayout(tree));
	let connections = $derived(generateConnections(renderNodes, currentPath));
	let treeWidth = $derived(Math.max(...renderNodes.map((n) => n.x), 0) + nodeWidth + 100);
	let treeHeight = $derived(Math.max(...renderNodes.map((n) => n.y), 0) + nodeHeight + 100);
</script>

{#if tree}
	<div class="tree-container">
		<svg width={treeWidth} height={treeHeight} viewBox="0 0 {treeWidth} {treeHeight}">
			<!-- Connections -->
			<g class="connections">
				{#each connections as connection}
					<path d={connection.path} class="tree-connection" class:active-path={connection.isActive} />
				{/each}
			</g>

			<!-- Nodes -->
			<g class="nodes">
				{#each renderNodes as node}
					<g
						transform="translate({node.x}, {node.y})"
						class="tree-node-group role-{node.role}"
						class:selected={selectedNode === node.uuid}
						onclick={() => handleNodeClick(node.uuid)}
						onkeydown={(e) => e.key === 'Enter' && handleNodeClick(node.uuid)}
						tabindex="0"
						role="button"
					>
						<rect
							class="tree-node role-{node.role}"
							class:selected={selectedNode === node.uuid}
							width={nodeWidth}
							height={nodeHeight}
							rx="8"
							ry="8"
						/>

						<foreignObject width={nodeWidth} height={nodeHeight} class="node-content">
							<div class="p-3 h-full flex flex-col">
								<div class="flex items-center justify-between mb-1">
									<div class="text-xs font-semibold role-label role-{node.role}">
										{node.role === 'user' ? 'ユーザー' : 'アシスタント'}
									</div>
									{#if node.children.length > 0}
										<div class="text-xs opacity-60">{node.children.length}個の分岐</div>
									{/if}
								</div>
								<div class="text-sm text-gray-700 line-clamp-3 flex-1">
									{truncateContent(node.content)}
								</div>
							</div>
						</foreignObject>
					</g>
				{/each}
			</g>
		</svg>
	</div>
{:else}
	<div class="empty-state">まだメッセージがありません</div>
{/if}

<style>
	.tree-container {
		width: 100%;
		min-height: 400px;
		overflow: auto;
		background-color: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
	}

	.tree-connection {
		stroke: #d1d5db;
		stroke-width: 2;
		fill: none;
	}

	.tree-connection.active-path {
		stroke: #3b82f6;
		stroke-width: 3;
	}

	.tree-node-group {
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.tree-node-group:hover .tree-node {
		stroke: #6b7280;
		stroke-width: 2;
	}

	.tree-node {
		fill: white;
		stroke: #e5e7eb;
		stroke-width: 1;
		transition: all 0.2s ease;
	}

	.tree-node.role-user {
		fill: #eff6ff;
		stroke: #3b82f6;
	}

	.tree-node.role-assistant {
		fill: #f0fdf4;
		stroke: #10b981;
	}

	.tree-node.selected {
		stroke-width: 3;
		filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
	}

	.tree-node.role-user.selected {
		stroke: #1d4ed8;
	}

	.tree-node.role-assistant.selected {
		stroke: #059669;
	}

	.node-content {
		pointer-events: none;
	}

	.role-label.role-user {
		color: #2563eb;
	}

	.role-label.role-assistant {
		color: #059669;
	}

	.empty-state {
		padding: 40px;
		text-align: center;
		color: #6b7280;
	}

	/* Utility classes */
	.p-3 {
		padding: 0.75rem;
	}
	.h-full {
		height: 100%;
	}
	.flex {
		display: flex;
	}
	.flex-col {
		flex-direction: column;
	}
	.flex-1 {
		flex: 1;
	}
	.items-center {
		align-items: center;
	}
	.justify-between {
		justify-content: space-between;
	}
	.mb-1 {
		margin-bottom: 0.25rem;
	}
	.text-xs {
		font-size: 0.75rem;
	}
	.text-sm {
		font-size: 0.875rem;
	}
	.font-semibold {
		font-weight: 600;
	}
	.opacity-60 {
		opacity: 0.6;
	}
	.text-gray-700 {
		color: #374151;
	}
	.line-clamp-3 {
		display: -webkit-box;
		-webkit-line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
