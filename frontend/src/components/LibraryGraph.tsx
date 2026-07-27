import { useEffect, useRef } from "react";
import cytoscape from "cytoscape";

interface NodeData {
  id: string;
  label: string;
  pages_count: number;
  reading_progress: number;
  added_at: string;
}

interface EdgeData {
  source: string;
  target: string;
  similarity: number;
}

interface LibraryGraphProps {
  nodes: NodeData[];
  edges: EdgeData[];
  threshold: number;
  onSelectNode: (nodeId: string, nodeLabel: string) => void;
}

export function LibraryGraph({ nodes, edges, threshold, onSelectNode }: LibraryGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Formatear nodos para Cytoscape
    const cyNodes = nodes.map((n) => ({
      data: {
        id: n.id,
        label: n.label.length > 20 ? n.label.substring(0, 17) + "..." : n.label,
        fullName: n.label,
        progress: n.reading_progress,
      },
    }));

    // Formatear aristas filtradas por el umbral de similitud
    const cyEdges = edges
      .filter((e) => e.similarity >= threshold)
      .map((e) => ({
        data: {
          id: `${e.source}-${e.target}`,
          source: e.source,
          target: e.target,
          weight: e.similarity,
        },
      }));

    // Inicializar Cytoscape
    const cy = cytoscape({
      container: containerRef.current,
      elements: [...cyNodes, ...cyEdges],
      boxSelectionEnabled: false,
      autoungrabify: false,
      style: [
        {
          selector: "node",
          style: {
            "background-color": "#4338ca",
            "border-width": "2px",
            "border-color": "#818cf8",
            width: "40px",
            height: "40px",
            label: "data(label)",
            color: "#e2e8f0",
            "font-size": "11px",
            "font-family": "Inter, system-ui, sans-serif",
            "text-valign": "bottom",
            "text-margin-y": 6,
            "text-halign": "center",
            "text-wrap": "wrap",
            "text-max-width": "100px",
            "overlay-opacity": 0,
            "transition-property": "background-color border-color",
            "transition-duration": 0.2,
          },
        },
        {
          selector: "edge",
          style: {
            width: "mapData(weight, 0.3, 1.0, 1.5, 7)",
            "line-color": "#818cf8",
            "curve-style": "bezier",
            opacity: "mapData(weight, 0.3, 1.0, 0.15, 0.95)",
            "overlay-opacity": 0,
          },
        },
        {
          selector: "node:selected",
          style: {
            "background-color": "#c084fc",
            "border-color": "#f3e8ff",
            "border-width": "3px",
          },
        },
      ],
      layout: {
        name: "cose",
        idealEdgeLength: () => 100,
        nodeOverlap: 20,
        refresh: 20,
        fit: true,
        padding: 40,
        randomize: false,
        componentSpacing: 100,
        nodeRepulsion: () => 400000,
        edgeElasticity: () => 100,
        nestingFactor: 5,
        gravity: 80,
        numIter: 1000,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0,
      } as any,
    });

    cyRef.current = cy;

    // Escuchar selección de nodos
    cy.on("tap", "node", (evt) => {
      const node = evt.target;
      onSelectNode(node.id(), node.data("fullName"));
    });

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [nodes, edges, threshold]);

  return (
    <div className="graph-container">
      <div ref={containerRef} className="cy-canvas" style={{ width: "100%", height: "100%" }} />
    </div>
  );
}
