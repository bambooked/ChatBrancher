<script>
  import { writable, derived } from 'svelte/store';

  // Sample tree data (mimicking the chat tree structure)
  const sampleTree = {
    uuid: 'root-1',
    role: 'user',
    content: 'Hello, can you help me with a coding problem?',
    children: [
      {
        uuid: 'node-2',
        role: 'assistant',
        content: 'Of course! I\'d be happy to help you with your coding problem. What specific issue are you working on?',
        children: [
          {
            uuid: 'node-3',
            role: 'user',
            content: 'I need to implement a tree visualization in Svelte',
            children: [
              {
                uuid: 'node-4',
                role: 'assistant',
                content: 'Great! Tree visualization in Svelte can be done using SVG elements. Here\'s how you can approach it...',
                children: []
              }
            ]
          },
          {
            uuid: 'node-5',
            role: 'user',
            content: 'Actually, let me try a different approach first',
            children: [
              {
                uuid: 'node-6',
                role: 'assistant',
                content: 'Sure! What alternative approach would you like to explore?',
                children: []
              }
            ]
          }
        ]
      }
    ]
  };

  // Store for selected node
  const selectedNode = writable('node-2');
  const currentPath = writable(['root-1', 'node-2']);

  // Configuration
  const nodeWidth = 180;
  const nodeHeight = 80;
  const horizontalSpacing = 240;
  const verticalSpacing = 120;

  // Calculate node positions (mimicking useTreeLayout)
  function calculateLayout(tree) {
    const nodes = [];
    
    function layoutNode(node, level = 0, parentX = 0, siblingIndex = 0, siblingCount = 1) {
      const xOffset = (siblingIndex - (siblingCount - 1) / 2) * horizontalSpacing;
      const x = level === 0 ? 150 : parentX + xOffset;
      const y = 50 + level * verticalSpacing;

      const renderNode = {
        ...node,
        x,
        y,
        level
      };

      nodes.push(renderNode);

      if (node.children.length > 0) {
        node.children.forEach((child, index) => {
          layoutNode(child, level + 1, x, index, node.children.length);
        });
      }
    }

    layoutNode(tree);
    return nodes;
  }

  // Generate connections between nodes
  function generateConnections(nodes, pathUuids) {
    const connections = [];
    
    function addConnections(node) {
      const parentNode = nodes.find(n => n.uuid === node.uuid);
      if (!parentNode) return;

      node.children.forEach(child => {
        const childNode = nodes.find(n => n.uuid === child.uuid);
        if (!childNode) return;

        const isActive = pathUuids.includes(node.uuid) && pathUuids.includes(child.uuid);
        const path = `M ${parentNode.x + nodeWidth / 2} ${parentNode.y + nodeHeight} L ${childNode.x + nodeWidth / 2} ${childNode.y}`;

        connections.push({
          from: node.uuid,
          to: child.uuid,
          path,
          isActive
        });

        addConnections(child);
      });
    }

    addConnections(sampleTree);
    return connections;
  }

  // Reactive calculations
  $: renderNodes = calculateLayout(sampleTree);
  $: connections = generateConnections(renderNodes, $currentPath);
  $: treeWidth = Math.max(...renderNodes.map(n => n.x)) + nodeWidth + 100;
  $: treeHeight = Math.max(...renderNodes.map(n => n.y)) + nodeHeight + 100;

  // Helper functions
  function getRoleColor(role) {
    switch (role) {
      case 'user': return 'text-blue-600';
      case 'assistant': return 'text-green-600';
      case 'system': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  }

  function getRoleLabel(role) {
    return role.charAt(0).toUpperCase() + role.slice(1);
  }

  function truncateContent(content, maxLength = 100) {
    return content.length > maxLength ? content.slice(0, maxLength) + '...' : content;
  }

  function handleNodeClick(nodeUuid) {
    selectedNode.set(nodeUuid);
    
    // Simple path calculation for demo
    const pathToNode = [];
    function findPath(node, target, path = []) {
      const currentPath = [...path, node.uuid];
      if (node.uuid === target) {
        pathToNode.push(...currentPath);
        return true;
      }
      
      for (let child of node.children) {
        if (findPath(child, target, currentPath)) {
          return true;
        }
      }
      return false;
    }
    
    findPath(sampleTree, nodeUuid);
    currentPath.set(pathToNode);
  }
</script>

<div class="tree-container">
  <svg width={treeWidth} height={treeHeight} viewBox="0 0 {treeWidth} {treeHeight}">
    <!-- Connections -->
    <g class="connections">
      {#each connections as connection}
        <path 
          d={connection.path} 
          class="tree-connection" 
          class:active-path={connection.isActive}
        />
      {/each}
    </g>
    
    <!-- Nodes -->
    <g class="nodes">
      {#each renderNodes as node}
        <g 
          transform="translate({node.x}, {node.y})"
          class="tree-node-group role-{node.role}"
          class:selected={$selectedNode === node.uuid}
          on:click={() => handleNodeClick(node.uuid)}
          on:keydown={(e) => e.key === 'Enter' && handleNodeClick(node.uuid)}
          tabindex="0"
          role="button"
        >
          <rect
            class="tree-node role-{node.role}"
            class:selected={$selectedNode === node.uuid}
            width={nodeWidth}
            height={nodeHeight}
            rx="8"
            ry="8"
          />
          
          <foreignObject width={nodeWidth} height={nodeHeight} class="node-content">
            <div class="p-3 h-full flex flex-col">
              <div class="flex items-center justify-between mb-1">
                <div class="text-xs font-semibold {getRoleColor(node.role)}">
                  {getRoleLabel(node.role)}
                </div>
                <div class="text-xs opacity-60">
                  {#if $selectedNode === node.uuid}
                    <span class="text-green-600">✅</span>
                  {:else}
                    <span class="text-blue-400">📍</span>
                  {/if}
                </div>
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

<style>
  .tree-container {
    width: 100%;
    height: 600px;
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

  .tree-node.role-system {
    fill: #f9fafb;
    stroke: #6b7280;
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

  .line-clamp-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  /* Utility classes */
  .p-3 { padding: 0.75rem; }
  .h-full { height: 100%; }
  .flex { display: flex; }
  .flex-col { flex-direction: column; }
  .flex-1 { flex: 1; }
  .items-center { align-items: center; }
  .justify-between { justify-content: space-between; }
  .mb-1 { margin-bottom: 0.25rem; }
  .text-xs { font-size: 0.75rem; }
  .text-sm { font-size: 0.875rem; }
  .font-semibold { font-weight: 600; }
  .opacity-60 { opacity: 0.6; }
  .text-blue-600 { color: #2563eb; }
  .text-green-600 { color: #059669; }
  .text-gray-600 { color: #4b5563; }
  .text-gray-700 { color: #374151; }
  .text-blue-400 { color: #60a5fa; }
</style>