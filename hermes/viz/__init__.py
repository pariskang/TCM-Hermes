"""Visualization — export disease knowledge as interactive ECharts HTML.

Self-contained HTML files (data embedded as JSON) rendering force-directed herb
networks, 病机→治法→药物 Sankey, co-occurrence heatmaps, frequency bars and
dynasty themeRiver timelines.  The dashboard bundles them with live DIY controls
(min edge weight, node-size metric, top-N, layout repulsion) that re-render in
the browser.  ECharts loads from a configurable CDN (or a local copy).
"""

from .echarts import VisualizationExporter, VizParams

__all__ = ["VisualizationExporter", "VizParams"]
