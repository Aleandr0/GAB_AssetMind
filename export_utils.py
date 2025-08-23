from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import os

class ReportGenerator:
    def __init__(self, portfolio_manager):
        self.portfolio_manager = portfolio_manager
        
    def generate_pdf_report(self, filename):
        """Genera un report PDF completo del portfolio"""
        try:
            doc = SimpleDocTemplate(filename, pagesize=A4, 
                                  rightMargin=2*cm, leftMargin=2*cm,
                                  topMargin=2*cm, bottomMargin=2*cm)
            
            # Raccolta dati
            df = self.portfolio_manager.load_data()
            summary = self.portfolio_manager.get_portfolio_summary()
            
            # Stili
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                textColor=colors.darkblue
            )
            
            # Contenuti del report
            story = []
            
            # Titolo
            story.append(Paragraph("GAB AssetMind - Report Portfolio", title_style))
            story.append(Paragraph(f"Generato il: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Sommario esecutivo
            story.append(Paragraph("Sommario Esecutivo", heading_style))
            
            summary_data = [
                ['Metrica', 'Valore'],
                ['Valore Totale Portfolio', f"€{summary['total_value']:,.2f}"],
                ['Reddito Annuale Totale', f"€{summary['total_income']:,.2f}"],
                ['Accumulo Mensile', f"€{summary['monthly_accumulation']:,.2f}"],
                ['Numero Totale Asset', str(len(df))]
            ]
            
            summary_table = Table(summary_data, colWidths=[8*cm, 6*cm])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Distribuzione per categoria
            story.append(Paragraph("Distribuzione per Categoria", heading_style))
            
            category_data = [['Categoria', 'Numero Asset', 'Percentuale']]
            total_assets = len(df)
            
            for category, count in summary['categories_count'].items():
                percentage = (count / total_assets * 100) if total_assets > 0 else 0
                category_data.append([category, str(count), f"{percentage:.1f}%"])
            
            category_table = Table(category_data, colWidths=[6*cm, 4*cm, 4*cm])
            category_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(category_table)
            story.append(Spacer(1, 20))
            
            # Dettaglio asset (primi 15)
            story.append(Paragraph("Dettaglio Asset Principali", heading_style))
            
            if not df.empty:
                # Ordina per valore totale attuale decrescente
                df_sorted = df.sort_values('updatedTotalValue', ascending=False, na_last=True).head(15)
                
                asset_data = [['Asset', 'Categoria', 'Valore Attuale', 'Reddito Annuo']]
                
                for _, row in df_sorted.iterrows():
                    current_value = row['updatedTotalValue'] if pd.notna(row['updatedTotalValue']) else row['createdTotalValue']
                    income = (row['incomePerYear'] if pd.notna(row['incomePerYear']) else 0) + \
                            (row['rentalIncome'] if pd.notna(row['rentalIncome']) else 0)
                    
                    asset_data.append([
                        str(row['assetName'])[:25] + '...' if len(str(row['assetName'])) > 25 else str(row['assetName']),
                        str(row['category']),
                        f"€{current_value:,.0f}" if pd.notna(current_value) else "€0",
                        f"€{income:,.0f}"
                    ])
                
                asset_table = Table(asset_data, colWidths=[5*cm, 3*cm, 3*cm, 3*cm])
                asset_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(asset_table)
            
            # Genera il PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"Errore nella generazione del PDF: {e}")
            return False
    
    def export_detailed_csv(self, filename):
        """Esporta CSV con calcoli aggiuntivi"""
        try:
            df = self.portfolio_manager.load_data()
            
            if df.empty:
                return False
            
            # Aggiungi colonne calcolate
            df['currentValue'] = df['updatedTotalValue'].fillna(df['createdTotalValue'])
            df['totalIncome'] = df['incomePerYear'].fillna(0) + df['rentalIncome'].fillna(0)
            df['performance'] = ((df['updatedTotalValue'] - df['createdTotalValue']) / df['createdTotalValue'] * 100).round(2)
            df['yieldPercentage'] = (df['totalIncome'] / df['currentValue'] * 100).round(2)
            
            # Riordina colonne
            columns_order = [
                'Id', 'category', 'assetName', 'position', 'riskLevel', 'ticker', 'isin',
                'createdAt', 'createdAmount', 'createdUnitPrice', 'createdTotalValue',
                'updatedAt', 'updatedAmount', 'updatedUnitPrice', 'updatedTotalValue',
                'currentValue', 'performance', 'totalIncome', 'yieldPercentage',
                'accumulationPlan', 'accumulationAmount', 'incomePerYear', 'rentalIncome', 'note'
            ]
            
            # Seleziona solo colonne esistenti
            existing_columns = [col for col in columns_order if col in df.columns]
            df_export = df[existing_columns]
            
            # Esporta
            df_export.to_csv(filename, index=False, encoding='utf-8-sig')
            return True
            
        except Exception as e:
            print(f"Errore nell'esportazione CSV: {e}")
            return False

class ChartGenerator:
    def __init__(self, portfolio_manager):
        self.portfolio_manager = portfolio_manager
    
    def save_category_pie_chart(self, filename):
        """Salva grafico a torta delle categorie"""
        try:
            df = self.portfolio_manager.load_data()
            
            if df.empty:
                return False
            
            category_counts = df['category'].value_counts()
            
            plt.figure(figsize=(10, 8))
            colors_list = plt.cm.Set3(range(len(category_counts)))
            
            plt.pie(category_counts.values, labels=category_counts.index, 
                   autopct='%1.1f%%', colors=colors_list, startangle=90)
            plt.title('Distribuzione Asset per Categoria', fontsize=16, fontweight='bold')
            plt.axis('equal')
            
            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            return True
            
        except Exception as e:
            print(f"Errore nella creazione del grafico: {e}")
            return False
    
    def save_value_bar_chart(self, filename):
        """Salva grafico a barre dei valori per categoria"""
        try:
            df = self.portfolio_manager.load_data()
            
            if df.empty:
                return False
            
            df['currentValue'] = df['updatedTotalValue'].fillna(df['createdTotalValue'])
            category_values = df.groupby('category')['currentValue'].sum().sort_values(ascending=False)
            
            plt.figure(figsize=(12, 8))
            bars = plt.bar(category_values.index, category_values.values, 
                          color=plt.cm.viridis(range(len(category_values))))
            
            plt.title('Valore Totale per Categoria', fontsize=16, fontweight='bold')
            plt.xlabel('Categoria', fontsize=12)
            plt.ylabel('Valore (€)', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            
            # Aggiungi valori sopra le barre
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'€{height:,.0f}',
                        ha='center', va='bottom', fontsize=10)
            
            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            return True
            
        except Exception as e:
            print(f"Errore nella creazione del grafico: {e}")
            return False
    
    def save_risk_distribution_chart(self, filename):
        """Salva grafico della distribuzione del rischio"""
        try:
            df = self.portfolio_manager.load_data()
            
            if df.empty:
                return False
            
            risk_counts = df['riskLevel'].value_counts().sort_index()
            risk_labels = ['Molto Basso', 'Basso', 'Medio', 'Alto', 'Molto Alto']
            colors = ['green', 'lightgreen', 'yellow', 'orange', 'red']
            
            plt.figure(figsize=(10, 6))
            bars = plt.bar(risk_counts.index, risk_counts.values, 
                          color=[colors[i-1] for i in risk_counts.index])
            
            plt.title('Distribuzione del Rischio nel Portfolio', fontsize=16, fontweight='bold')
            plt.xlabel('Livello di Rischio', fontsize=12)
            plt.ylabel('Numero di Asset', fontsize=12)
            
            # Personalizza le etichette dell'asse x
            plt.xticks(range(1, 6), [risk_labels[i-1] for i in range(1, 6)])
            
            # Aggiungi valori sopra le barre
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom', fontsize=12)
            
            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            return True
            
        except Exception as e:
            print(f"Errore nella creazione del grafico: {e}")
            return False