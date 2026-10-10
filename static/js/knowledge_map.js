/**
 * Cognimap AI - Interactive Visual Knowledge Map
 * Powered by Cytoscape.js
 */

let cy = null;
let currentMapData = null;

function initKnowledgeMap(containerId, studentId = null) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const url = studentId ? `/api/knowledge-map?student_id=${studentId}` : '/api/knowledge-map';

  fetch(url)
    .then(res => res.json())
    .then(data => {
      currentMapData = data;
      renderCytoscape(container, data);
      setupControls();
    })
    .catch(err => {
      console.error("Failed to load knowledge map data:", err);
      container.innerHTML = `<div style="padding: 2.5rem; text-align: center; color: var(--status-weak);">Failed to load Knowledge Map elements.</div>`;
    });
}

function renderCytoscape(container, graphData) {
  // Define Node Colors according to Status
  const colorMap = {
    'Strong': '#10b981',
    'Needs Improvement': '#f59e0b',
    'Weak': '#f43f5e',
    'Unassessed': '#334155'
  };

  const elements = [
    ...graphData.nodes.map(n => ({
      data: {
        ...n.data,
        color: colorMap[n.data.status] || '#6366f1',
        label: `${n.data.name}\n${n.data.score !== null ? n.data.score + '%' : 'Unassessed'}`
      }
    })),
    ...graphData.edges
  ];

  cy = cytoscape({
    container: container,
    elements: elements,
    style: [
      {
        selector: 'node',
        style: {
          'background-color': 'data(color)',
          'label': 'data(label)',
          'color': '#ffffff',
          'text-valign': 'center',
          'text-halign': 'center',
          'text-wrap': 'wrap',
          'text-max-width': '105px',
          'font-family': 'Plus Jakarta Sans, sans-serif',
          'font-size': '11px',
          'font-weight': '700',
          'width': '88px',
          'height': '88px',
          'border-width': 3,
          'border-color': 'rgba(255, 255, 255, 0.45)',
          'overlay-opacity': 0,
          'transition-property': 'background-color, border-color, width, height, shadow-blur',
          'transition-duration': '0.2s',
          'shadow-blur': 18,
          'shadow-color': 'data(color)',
          'shadow-opacity': 0.55
        }
      },
      {
        selector: 'node:selected',
        style: {
          'border-width': 5,
          'border-color': '#ffffff',
          'width': '96px',
          'height': '96px',
          'shadow-blur': 32,
          'shadow-opacity': 0.95
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 2.5,
          'line-color': 'rgba(148, 163, 184, 0.35)',
          'target-arrow-color': 'rgba(148, 163, 184, 0.65)',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'arrow-scale': 1.25,
          'overlay-opacity': 0
        }
      },
      {
        selector: 'edge.highlighted',
        style: {
          'line-color': '#6366f1',
          'target-arrow-color': '#6366f1',
          'width': 4
        }
      }
    ],
    layout: {
      name: 'breadthfirst',
      directed: true,
      roots: (graphData.roots && graphData.roots.length > 0) ? graphData.roots : undefined,
      padding: 50,
      spacingFactor: 1.45,
      animate: true,
      animationDuration: 600
    },
    wheelSensitivity: 0.25
  });

  // Handle Node Click
  cy.on('tap', 'node', function(evt) {
    const node = evt.target;
    const nodeData = node.data();
    openInspector(nodeData);

    // Highlight incoming and outgoing edges
    cy.edges().removeClass('highlighted');
    node.connectedEdges().addClass('highlighted');
  });

  // Handle background click (close drawer)
  cy.on('tap', function(evt) {
    if (evt.target === cy) {
      closeInspector();
      cy.edges().removeClass('highlighted');
    }
  });
}

function openInspector(data) {
  const drawer = document.getElementById('map-inspector');
  if (!drawer) return;

  const statusClass = data.status === 'Strong' ? 'badge-strong' : (data.status === 'Weak' ? 'badge-weak' : (data.status === 'Needs Improvement' ? 'badge-ni' : 'badge-unassessed'));

  const prereqsHtml = (data.prerequisites && data.prerequisites.length > 0)
    ? data.prerequisites.map(p => `<span class="badge badge-unassessed" style="margin: 2px;">${p}</span>`).join(' ')
    : '<span style="color: var(--text-dim); font-size: 0.85rem;">None (Foundational Root)</span>';

  const dependentsHtml = (data.dependents && data.dependents.length > 0)
    ? data.dependents.map(d => `<span class="badge badge-unassessed" style="margin: 2px;">${d}</span>`).join(' ')
    : '<span style="color: var(--text-dim); font-size: 0.85rem;">None (Terminal Concept)</span>';

  let codeBlock = '';
  if (data.code_example) {
    codeBlock = `
      <div style="margin-top: 1.15rem;">
        <div style="font-size: 0.78rem; text-transform: uppercase; color: var(--text-dim); margin-bottom: 0.35rem; font-weight: 700; letter-spacing: 0.05em;">Code Reference:</div>
        <pre style="background: rgba(7,10,17,0.85); padding: 0.85rem; border-radius: 8px; font-size: 0.82rem; overflow-x: auto; border: 1px solid var(--border-subtle); color: #cbd5e1; line-height: 1.45;"><code>${escapeHtml(data.code_example)}</code></pre>
      </div>
    `;
  }

  drawer.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem;">
      <div>
        <span class="badge ${statusClass}" style="margin-bottom: 0.45rem;">
          <span class="badge-dot"></span> ${data.status} ${data.score !== null ? '(' + data.score + '%)' : ''}
        </span>
        <h3 style="font-size: 1.35rem; font-weight: 800; color: var(--text-main); letter-spacing: -0.02em;">${data.name}</h3>
        <div style="font-size: 0.84rem; color: var(--text-muted); margin-top: 0.2rem;">${data.unit || ''} &bull; ${data.topic || ''}</div>
      </div>
      <button onclick="closeInspector()" class="btn btn-secondary btn-sm" style="padding: 0.35rem 0.65rem; border-radius: 6px;">✕</button>
    </div>

    <div style="margin-bottom: 1.15rem;">
      <div style="font-size: 0.78rem; text-transform: uppercase; color: var(--text-dim); margin-bottom: 0.35rem; font-weight: 700; letter-spacing: 0.05em;">Description:</div>
      <p style="font-size: 0.9rem; color: var(--text-muted); line-height: 1.55;">${data.description || 'No description available.'}</p>
    </div>

    <div style="margin-bottom: 1.15rem;">
      <div style="font-size: 0.78rem; text-transform: uppercase; color: var(--text-dim); margin-bottom: 0.4rem; font-weight: 700; letter-spacing: 0.05em;">Prerequisite Dependencies:</div>
      <div style="display: flex; flex-wrap: wrap; gap: 4px;">${prereqsHtml}</div>
    </div>

    <div style="margin-bottom: 1.15rem;">
      <div style="font-size: 0.78rem; text-transform: uppercase; color: var(--text-dim); margin-bottom: 0.4rem; font-weight: 700; letter-spacing: 0.05em;">Directly Enables Concepts:</div>
      <div style="display: flex; flex-wrap: wrap; gap: 4px;">${dependentsHtml}</div>
    </div>

    ${data.key_points ? `
      <div style="margin-bottom: 1.15rem; background: rgba(16, 185, 129, 0.06); border: 1px solid rgba(16, 185, 129, 0.2); padding: 0.85rem 1rem; border-radius: 8px;">
        <div style="font-size: 0.78rem; text-transform: uppercase; color: var(--status-strong); margin-bottom: 0.25rem; font-weight: 700; letter-spacing: 0.05em;">Key Takeaway:</div>
        <p style="font-size: 0.86rem; color: #a7f3d0; line-height: 1.5;">${data.key_points}</p>
      </div>
    ` : ''}

    ${codeBlock}

    <div style="margin-top: 1.5rem; display: flex; gap: 0.5rem;">
      <a href="/learning-path#concept-${data.id}" class="btn btn-primary btn-sm" style="flex: 1;">
        Study Material &rarr;
      </a>
      <button onclick="closeInspector()" class="btn btn-secondary btn-sm">Close</button>
    </div>
  `;

  drawer.style.display = 'block';
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
}

function closeInspector() {
  const drawer = document.getElementById('map-inspector');
  if (drawer) drawer.style.display = 'none';
}

function setupControls() {
  const zoomInBtn = document.getElementById('btn-zoom-in');
  const zoomOutBtn = document.getElementById('btn-zoom-out');
  const fitBtn = document.getElementById('btn-fit-map');
  const filterSelect = document.getElementById('filter-status-select');

  if (zoomInBtn) zoomInBtn.onclick = () => cy && cy.zoom(cy.zoom() * 1.25);
  if (zoomOutBtn) zoomOutBtn.onclick = () => cy && cy.zoom(cy.zoom() * 0.8);
  if (fitBtn) fitBtn.onclick = () => cy && cy.fit(null, 40);

  if (filterSelect) {
    filterSelect.onchange = (e) => {
      const val = e.target.value;
      if (!cy) return;
      if (val === 'all') {
        cy.nodes().show();
      } else {
        cy.nodes().forEach(node => {
          if (node.data('status') === val) {
            node.show();
          } else {
            node.hide();
          }
        });
      }
    };
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
