#!/usr/bin/env python3
"""
GAB AssetMind - Dependency Graph Visualization
Crea un grafico delle dipendenze tra i file del progetto
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
from matplotlib.patches import FancyBboxPatch
import numpy as np

def create_dependency_graph():
    """Crea e visualizza il grafico delle dipendenze"""
    
    # Crea il grafo diretto
    G = nx.DiGraph()
    
    # Definizione nodi con categorie
    nodes = {
        # Entry Points
        'User': {'category': 'entry', 'label': 'User\nLaunch'},
        'GAB_AssetMind.pyw': {'category': 'entry', 'label': 'GAB_AssetMind.pyw\n(Launcher)'},
        
        # Core Application
        'main_refactored.py': {'category': 'core', 'label': 'main_refactored.py\nGABAssetMind Class'},
        
        # Configuration & Business Logic
        'config.py': {'category': 'config', 'label': 'config.py\nUIConfig, Messages'},
        'models.py': {'category': 'config', 'label': 'models.py\nPortfolioManager, Asset'},
        'utils.py': {'category': 'config', 'label': 'utils.py\nValidators, Formatters'},
        'export_utils.py': {'category': 'config', 'label': 'export_utils.py\nPDF/CSV Export'},
        
        # UI Components
        'ui_components.py': {'category': 'ui', 'label': 'ui_components.py\nNavBar, PortfolioTable'},
        'asset_form.py': {'category': 'ui', 'label': 'asset_form.py\nAssetForm, FormState'},
        'charts_ui.py': {'category': 'ui', 'label': 'charts_ui.py\nChartsUI'},
        'export_ui.py': {'category': 'ui', 'label': 'export_ui.py\nExportUI'},
        
        # Data
        'portfolio_data.xlsx': {'category': 'data', 'label': 'portfolio_data.xlsx\n27 Assets'},
        
        # Configuration Files
        'requirements.txt': {'category': 'docs', 'label': 'requirements.txt\nDependencies'},
        '.gitignore': {'category': 'docs', 'label': '.gitignore\nVCS Config'},
        'README.md': {'category': 'docs', 'label': 'README.md\nDocumentation'},
        'ARCHITECTURE.md': {'category': 'docs', 'label': 'ARCHITECTURE.md\nTech Docs'}
    }
    
    # Aggiungi nodi al grafo
    for node_id, node_info in nodes.items():
        G.add_node(node_id, **node_info)
    
    # Definizione collegamenti (dipendenze)
    edges = [
        # Entry flow
        ('User', 'GAB_AssetMind.pyw'),
        ('GAB_AssetMind.pyw', 'main_refactored.py'),
        
        # Core dependencies
        ('main_refactored.py', 'config.py'),
        ('main_refactored.py', 'models.py'),
        ('main_refactored.py', 'utils.py'),
        ('main_refactored.py', 'ui_components.py'),
        ('main_refactored.py', 'asset_form.py'),
        ('main_refactored.py', 'charts_ui.py'),
        ('main_refactored.py', 'export_ui.py'),
        
        # UI Component dependencies
        ('ui_components.py', 'config.py'),
        ('ui_components.py', 'utils.py'),
        ('ui_components.py', 'models.py'),
        
        ('asset_form.py', 'config.py'),
        ('asset_form.py', 'utils.py'),
        ('asset_form.py', 'models.py'),
        
        ('charts_ui.py', 'config.py'),
        ('charts_ui.py', 'models.py'),
        
        ('export_ui.py', 'config.py'),
        ('export_ui.py', 'models.py'),
        ('export_ui.py', 'utils.py'),
        ('export_ui.py', 'export_utils.py'),
        
        # Data access
        ('models.py', 'portfolio_data.xlsx'),
        
        # Documentation connections (dotted)
        ('config.py', 'requirements.txt'),
    ]
    
    # Aggiungi archi al grafo
    G.add_edges_from(edges)
    
    # Configurazione colori per categoria
    colors = {
        'entry': '#e1f5fe',      # Light Blue
        'core': '#f3e5f5',       # Light Purple
        'config': '#fff3e0',     # Light Orange
        'ui': '#e8f5e8',         # Light Green
        'data': '#fce4ec',       # Light Pink
        'docs': '#f1f8e9'        # Light Lime
    }
    
    # Crea il layout del grafo
    plt.figure(figsize=(16, 12))
    
    # Layout gerarchico personalizzato
    pos = {}
    
    # Layer 1: Entry Points
    pos['User'] = (0, 6)
    pos['GAB_AssetMind.pyw'] = (0, 5)
    
    # Layer 2: Core
    pos['main_refactored.py'] = (0, 3.5)
    
    # Layer 3: Configuration & Business Logic (centro-sinistra)
    pos['config.py'] = (-3, 2)
    pos['models.py'] = (-1, 2)
    pos['utils.py'] = (1, 2)
    pos['export_utils.py'] = (3, 2)
    
    # Layer 4: UI Components (centro-destra)
    pos['ui_components.py'] = (-3, 0.5)
    pos['asset_form.py'] = (-1, 0.5)
    pos['charts_ui.py'] = (1, 0.5)
    pos['export_ui.py'] = (3, 0.5)
    
    # Layer 5: Data
    pos['portfolio_data.xlsx'] = (0, -1)
    
    # Layer 6: Documentation (bottom)
    pos['requirements.txt'] = (-4, -2.5)
    pos['.gitignore'] = (-2, -2.5)
    pos['README.md'] = (2, -2.5)
    pos['ARCHITECTURE.md'] = (4, -2.5)
    
    # Disegna i nodi
    for node, (x, y) in pos.items():
        node_info = nodes[node]
        color = colors[node_info['category']]
        
        # Disegna il nodo
        nx.draw_networkx_nodes(G, pos, nodelist=[node], 
                              node_color=color, 
                              node_size=3000,
                              node_shape='o')
        
        # Aggiungi etichetta
        plt.text(x, y, node_info['label'], 
                ha='center', va='center', 
                fontsize=8, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.8))
    
    # Disegna gli archi
    nx.draw_networkx_edges(G, pos, 
                          edge_color='gray', 
                          arrows=True, 
                          arrowsize=20, 
                          arrowstyle='->', 
                          alpha=0.6,
                          width=1.5)
    
    # Aggiungi legenda
    legend_elements = [
        mpatches.Patch(color=colors['entry'], label='Entry Points'),
        mpatches.Patch(color=colors['core'], label='Core Application'),
        mpatches.Patch(color=colors['config'], label='Config & Business Logic'),
        mpatches.Patch(color=colors['ui'], label='UI Components'),
        mpatches.Patch(color=colors['data'], label='Data Layer'),
        mpatches.Patch(color=colors['docs'], label='Documentation & Config')
    ]
    
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0.02, 0.98))
    
    # Configurazione grafico
    plt.title('GAB AssetMind - Dependency Graph\nArchitettura Modulare (15 Files)', 
              fontsize=16, fontweight='bold', pad=20)
    
    plt.axis('off')
    plt.tight_layout()
    
    # Salva il grafico
    plt.savefig('GAB_AssetMind_Dependencies.png', dpi=300, bbox_inches='tight')
    plt.close()  # Chiude la figura senza mostrare

def create_simple_flow_chart():
    """Crea un diagramma di flusso semplificato"""
    
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Definizione box e posizioni
    boxes = {
        'User Launch': {'pos': (7, 9), 'color': '#e1f5fe', 'size': (2, 0.8)},
        'GAB_AssetMind.pyw': {'pos': (7, 7.5), 'color': '#e1f5fe', 'size': (2.5, 0.8)},
        'main_refactored.py': {'pos': (7, 6), 'color': '#f3e5f5', 'size': (3, 0.8)},
        
        'config.py': {'pos': (2, 4.5), 'color': '#fff3e0', 'size': (2, 0.8)},
        'models.py': {'pos': (5, 4.5), 'color': '#fff3e0', 'size': (2, 0.8)},
        'utils.py': {'pos': (8, 4.5), 'color': '#fff3e0', 'size': (2, 0.8)},
        'export_utils.py': {'pos': (11, 4.5), 'color': '#fff3e0', 'size': (2.5, 0.8)},
        
        'ui_components.py': {'pos': (2, 3), 'color': '#e8f5e8', 'size': (2.5, 0.8)},
        'asset_form.py': {'pos': (5, 3), 'color': '#e8f5e8', 'size': (2, 0.8)},
        'charts_ui.py': {'pos': (8, 3), 'color': '#e8f5e8', 'size': (2, 0.8)},
        'export_ui.py': {'pos': (11, 3), 'color': '#e8f5e8', 'size': (2, 0.8)},
        
        'portfolio_data.xlsx': {'pos': (7, 1.5), 'color': '#fce4ec', 'size': (3, 0.8)},
        
        'Documentation': {'pos': (7, 0.3), 'color': '#f1f8e9', 'size': (4, 0.6)},
    }
    
    # Disegna i box
    for name, info in boxes.items():
        x, y = info['pos']
        w, h = info['size']
        
        # Box principale
        box = FancyBboxPatch((x-w/2, y-h/2), w, h,
                           boxstyle="round,pad=0.1",
                           facecolor=info['color'],
                           edgecolor='black',
                           linewidth=1.5)
        ax.add_patch(box)
        
        # Testo
        ax.text(x, y, name, ha='center', va='center', 
                fontsize=10, fontweight='bold')
    
    # Disegna le frecce
    arrows = [
        ((7, 8.6), (7, 8.3)),  # User -> Launcher
        ((7, 7.1), (7, 6.8)),  # Launcher -> Main
        
        # Main -> Config layer
        ((6, 5.6), (3, 5.3)),  # Main -> config
        ((6.5, 5.6), (5, 5.3)),  # Main -> models  
        ((7.5, 5.6), (8, 5.3)),  # Main -> utils
        ((8, 5.6), (10.5, 5.3)),  # Main -> export_utils
        
        # Main -> UI layer
        ((6, 5.6), (3, 3.8)),  # Main -> ui_components
        ((6.5, 5.6), (5, 3.8)),  # Main -> asset_form
        ((7.5, 5.6), (8, 3.8)),  # Main -> charts
        ((8, 5.6), (11, 3.8)),  # Main -> export_ui
        
        # Models -> Data
        ((5, 4.1), (6, 2.3)),  # models -> data
    ]
    
    for start, end in arrows:
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', lw=2, color='gray', alpha=0.7))
    
    # Etichette delle sezioni
    ax.text(0.5, 4.5, 'Config &\nBusiness Logic', ha='center', va='center',
            fontsize=12, fontweight='bold', color='#bf5700', rotation=90)
    ax.text(0.5, 3, 'UI\nComponents', ha='center', va='center',
            fontsize=12, fontweight='bold', color='#2d5016', rotation=90)
    
    # Configurazione assi
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Titolo
    plt.title('GAB AssetMind - Architecture Flow\nModular Design (15 Files)', 
              fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('GAB_AssetMind_Flow.png', dpi=300, bbox_inches='tight')
    plt.close()  # Chiude la figura senza mostrare

if __name__ == "__main__":
    print("Creazione grafici delle dipendenze...")
    
    # Crea entrambi i grafici
    create_dependency_graph()
    create_simple_flow_chart()
    
    print("Grafici salvati:")
    print("- GAB_AssetMind_Dependencies.png (Grafo completo)")
    print("- GAB_AssetMind_Flow.png (Diagramma di flusso)")