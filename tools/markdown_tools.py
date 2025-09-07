# -*- coding: utf-8 -*-
# tools/markdown_tools.py
import logging
import re
from datetime import datetime

def register_tools(mcp):
    """Registra i tool Markdown con l'istanza del server MCP."""
    logging.info("📝 Registrazione tool-set: Markdown Tools")

    @mcp.tool()
    def markdown_to_html(markdown_text: str) -> str:
        """
        Converte testo Markdown in HTML (conversione semplificata).
        
        Args:
            markdown_text: Testo Markdown da convertire
        """
        try:
            html = markdown_text
            
            # Headers
            html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
            html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
            html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
            html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
            
            # Bold e Italic
            html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
            html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
            html = re.sub(r'__(.+?)__', r'<strong>\1</strong>', html)
            html = re.sub(r'_(.+?)_', r'<em>\1</em>', html)
            
            # Code inline e block
            html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
            html = re.sub(r'^```\n(.+?)\n```', r'<pre><code>\1</code></pre>', html, flags=re.MULTILINE | re.DOTALL)
            
            # Links
            html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)
            
            # Images
            html = re.sub(r'!\[(.+?)\]\((.+?)\)', r'<img src="\2" alt="\1" />', html)
            
            # Lists
            lines = html.split('\n')
            in_ul = False
            in_ol = False
            result_lines = []
            
            for line in lines:
                stripped = line.strip()
                
                # Unordered list
                if re.match(r'^[-*+] ', stripped):
                    if not in_ul:
                        result_lines.append('<ul>')
                        in_ul = True
                    if in_ol:
                        result_lines.append('</ol>')
                        in_ol = False
                    content = re.sub(r'^[-*+] ', '', stripped)
                    result_lines.append(f'  <li>{content}</li>')
                
                # Ordered list
                elif re.match(r'^\d+\. ', stripped):
                    if not in_ol:
                        result_lines.append('<ol>')
                        in_ol = True
                    if in_ul:
                        result_lines.append('</ul>')
                        in_ul = False
                    content = re.sub(r'^\d+\. ', '', stripped)
                    result_lines.append(f'  <li>{content}</li>')
                
                # End lists
                else:
                    if in_ul:
                        result_lines.append('</ul>')
                        in_ul = False
                    if in_ol:
                        result_lines.append('</ol>')
                        in_ol = False
                    
                    # Paragraphs
                    if stripped and not stripped.startswith('<'):
                        result_lines.append(f'<p>{stripped}</p>')
                    elif stripped.startswith('<'):
                        result_lines.append(stripped)
                    else:
                        result_lines.append('')
            
            # Close any open lists
            if in_ul:
                result_lines.append('</ul>')
            if in_ol:
                result_lines.append('</ol>')
            
            html_output = '\n'.join(result_lines)
            
            # Blockquotes
            html_output = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html_output, flags=re.MULTILINE)
            
            # Horizontal rules
            html_output = re.sub(r'^---+$', r'<hr>', html_output, flags=re.MULTILINE)
            
            return f"""📝 MARKDOWN → HTML
Lunghezza input: {len(markdown_text)} caratteri
Lunghezza output: {len(html_output)} caratteri

HTML GENERATO:
{html_output}

💡 NOTA: Questa è una conversione semplificata. Per progetti complessi, usa librerie specializzate come markdown2 o mistune."""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def generate_markdown_table(headers: str, data: str, alignment: str = "left") -> str:
        """
        Genera una tabella Markdown da dati strutturati.
        
        Args:
            headers: Intestazioni separate da virgola
            data: Righe di dati, formato "riga1col1,riga1col2;riga2col1,riga2col2"
            alignment: Allineamento (left, center, right)
        """
        try:
            # Parse headers
            header_list = [h.strip() for h in headers.split(',')]
            
            # Parse data
            if not data.strip():
                data_rows = []
            else:
                data_rows = []
                for row in data.split(';'):
                    if row.strip():
                        cols = [col.strip() for col in row.split(',')]
                        # Assicura che ogni riga abbia il numero giusto di colonne
                        while len(cols) < len(header_list):
                            cols.append('')
                        data_rows.append(cols[:len(header_list)])
            
            # Calcola larghezza massima per ogni colonna
            col_widths = []
            for i, header in enumerate(header_list):
                max_width = len(header)
                for row in data_rows:
                    if i < len(row):
                        max_width = max(max_width, len(str(row[i])))
                col_widths.append(max_width)
            
            # Crea la tabella
            table_lines = []
            
            # Header row
            header_row = '| ' + ' | '.join(header.ljust(col_widths[i]) for i, header in enumerate(header_list)) + ' |'
            table_lines.append(header_row)
            
            # Separator row
            separators = []
            for width in col_widths:
                if alignment == "center":
                    sep = ":" + "-" * (width - 2) + ":"
                elif alignment == "right":
                    sep = "-" * (width - 1) + ":"
                else:  # left
                    sep = "-" * width
                separators.append(sep)
            
            separator_row = '| ' + ' | '.join(separators) + ' |'
            table_lines.append(separator_row)
            
            # Data rows
            for row in data_rows:
                data_row = '| ' + ' | '.join(str(row[i]).ljust(col_widths[i]) if i < len(row) else ''.ljust(col_widths[i]) for i in range(len(header_list))) + ' |'
                table_lines.append(data_row)
            
            table_md = '\n'.join(table_lines)
            
            return f"""📊 TABELLA MARKDOWN GENERATA
Colonne: {len(header_list)}
Righe dati: {len(data_rows)}
Allineamento: {alignment}

TABELLA:
{table_md}

PREVIEW HTML:
<table>
<thead>
<tr>{''.join(f'<th>{h}</th>' for h in header_list)}</tr>
</thead>
<tbody>
{''.join('<tr>' + ''.join(f'<td>{row[i] if i < len(row) else ""}</td>' for i in range(len(header_list))) + '</tr>' for row in data_rows)}
</tbody>
</table>"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def analyze_markdown_structure(markdown_text: str) -> str:
        """
        Analizza la struttura di un documento Markdown.
        
        Args:
            markdown_text: Testo Markdown da analizzare
        """
        try:
            lines = markdown_text.split('\n')
            
            # Contatori
            stats = {
                'headers': {'h1': 0, 'h2': 0, 'h3': 0, 'h4': 0, 'h5': 0, 'h6': 0},
                'links': 0,
                'images': 0,
                'code_blocks': 0,
                'inline_code': 0,
                'lists': {'ul': 0, 'ol': 0},
                'tables': 0,
                'blockquotes': 0,
                'horizontal_rules': 0,
                'paragraphs': 0,
                'words': 0,
                'chars': len(markdown_text)
            }
            
            # Analiza linea per linea
            in_code_block = False
            current_list_type = None
            
            for line in lines:
                stripped = line.strip()
                
                # Headers
                if stripped.startswith('#'):
                    level = len(re.match(r'^#+', stripped).group())
                    if level <= 6:
                        stats['headers'][f'h{level}'] += 1
                
                # Code blocks
                if stripped.startswith('```'):
                    if not in_code_block:
                        stats['code_blocks'] += 1
                        in_code_block = True
                    else:
                        in_code_block = False
                    continue
                
                if in_code_block:
                    continue
                
                # Lists
                if re.match(r'^[-*+] ', stripped):
                    if current_list_type != 'ul':
                        stats['lists']['ul'] += 1
                        current_list_type = 'ul'
                elif re.match(r'^\d+\. ', stripped):
                    if current_list_type != 'ol':
                        stats['lists']['ol'] += 1
                        current_list_type = 'ol'
                else:
                    current_list_type = None
                
                # Tables (simplified detection)
                if '|' in stripped and len(stripped.split('|')) > 2:
                    stats['tables'] += 1
                
                # Blockquotes
                if stripped.startswith('>'):
                    stats['blockquotes'] += 1
                
                # Horizontal rules
                if re.match(r'^---+$', stripped):
                    stats['horizontal_rules'] += 1
                
                # Paragraphs (simple heuristic)
                if stripped and not any([
                    stripped.startswith('#'),
                    stripped.startswith('>'),
                    stripped.startswith('```'),
                    re.match(r'^[-*+] ', stripped),
                    re.match(r'^\d+\. ', stripped),
                    '|' in stripped
                ]):
                    stats['paragraphs'] += 1
            
            # Analizza inline elements
            stats['links'] = len(re.findall(r'\[.+?\]\(.+?\)', markdown_text))
            stats['images'] = len(re.findall(r'!\[.+?\]\(.+?\)', markdown_text))
            stats['inline_code'] = len(re.findall(r'`[^`]+`', markdown_text))
            
            # Word count
            text_content = re.sub(r'[#*_`\[\]()!]', '', markdown_text)
            text_content = re.sub(r'\s+', ' ', text_content)
            words = text_content.split()
            stats['words'] = len([w for w in words if w.strip()])
            
            # Estrae struttura headers
            header_structure = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('#'):
                    level = len(re.match(r'^#+', stripped).group())
                    title = re.sub(r'^#+\s*', '', stripped)
                    header_structure.append((level, title))
            
            result = f"""📖 ANALISI STRUTTURA MARKDOWN
Caratteri totali: {stats['chars']:,}
Parole: {stats['words']:,}
Linee: {len(lines):,}

ELEMENTI STRUTTURALI:
Headers:
  H1: {stats['headers']['h1']}
  H2: {stats['headers']['h2']}
  H3: {stats['headers']['h3']}
  H4: {stats['headers']['h4']}
  H5: {stats['headers']['h5']}
  H6: {stats['headers']['h6']}

Contenuto:
  Paragrafi: {stats['paragraphs']}
  Liste non ordinate: {stats['lists']['ul']}
  Liste ordinate: {stats['lists']['ol']}
  Tabelle: {stats['tables']}
  Citazioni: {stats['blockquotes']}
  Linee orizzontali: {stats['horizontal_rules']}

Codice:
  Blocchi di codice: {stats['code_blocks']}
  Codice inline: {stats['inline_code']}

Media:
  Links: {stats['links']}
  Immagini: {stats['images']}

STRUTTURA HEADERS:"""
            
            if header_structure:
                for level, title in header_structure[:20]:  # Primi 20 headers
                    indent = "  " * (level - 1)
                    result += f"\n{indent}{'#' * level} {title[:60]}{'...' if len(title) > 60 else ''}"
                
                if len(header_structure) > 20:
                    result += f"\n... e altri {len(header_structure) - 20} headers"
            else:
                result += "\nNessun header trovato"
            
            # Suggerimenti
            suggestions = []
            if stats['headers']['h1'] == 0:
                suggestions.append("Considera di aggiungere un titolo principale (H1)")
            if stats['headers']['h1'] > 1:
                suggestions.append("Hai più titoli H1, considera di usare H2 per sottosezioni")
            if stats['words'] > 2000 and sum(stats['headers'].values()) < 5:
                suggestions.append("Documento lungo: considera di aggiungere più headers per organizzare il contenuto")
            if stats['links'] == 0 and stats['words'] > 500:
                suggestions.append("Considera di aggiungere link di riferimento")
            
            if suggestions:
                result += "\n\n💡 SUGGERIMENTI:\n" + '\n'.join(f"- {s}" for s in suggestions)
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def generate_markdown_toc(markdown_text: str, max_level: int = 3) -> str:
        """
        Genera un indice (Table of Contents) per un documento Markdown.
        
        Args:
            markdown_text: Testo Markdown
            max_level: Livello massimo di header da includere (1-6)
        """
        try:
            lines = markdown_text.split('\n')
            headers = []
            
            # Estrae headers
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('#'):
                    level = len(re.match(r'^#+', stripped).group())
                    if level <= max_level:
                        title = re.sub(r'^#+\s*', '', stripped)
                        # Crea anchor (simplified)
                        anchor = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
                        anchor = re.sub(r'\s+', '-', anchor.strip())
                        headers.append((level, title, anchor))
            
            if not headers:
                return "❌ Nessun header trovato nel documento"
            
            # Genera TOC
            toc_lines = ["## Indice", ""]
            
            for level, title, anchor in headers:
                indent = "  " * (level - 1)
                toc_lines.append(f"{indent}- [{title}](#{anchor})")
            
            toc_md = '\n'.join(toc_lines)
            
            # Versione con numerazione
            toc_numbered_lines = ["## Indice", ""]
            counters = [0] * 6  # Per 6 livelli di headers
            
            for level, title, anchor in headers:
                # Aggiorna contatori
                counters[level - 1] += 1
                # Reset contatori livelli inferiori
                for i in range(level, 6):
                    counters[i] = 0
                
                # Crea numerazione
                numbering = '.'.join(str(counters[i]) for i in range(level) if counters[i] > 0)
                
                indent = "  " * (level - 1)
                toc_numbered_lines.append(f"{indent}{numbering}. [{title}](#{anchor})")
            
            toc_numbered = '\n'.join(toc_numbered_lines)
            
            return f"""📑 INDICE MARKDOWN GENERATO
Headers trovati: {len(headers)}
Livello massimo: {max_level}

INDICE SEMPLICE:
{toc_md}

INDICE NUMERATO:
{toc_numbered}

💡 ISTRUZIONI:
1. Copia l'indice che preferisci
2. Incollalo all'inizio del documento
3. Assicurati che gli anchor link funzionino nel tuo renderer Markdown
4. Alcuni renderer potrebbero generare anchor automaticamente diversi"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def format_markdown_document(title: str, author: str, content: str, include_metadata: bool = True) -> str:
        """
        Formatta un documento Markdown completo con metadata e struttura.
        
        Args:
            title: Titolo del documento
            author: Autore del documento
            content: Contenuto principale
            include_metadata: Se includere metadata YAML frontmatter
        """
        try:
            formatted_doc = ""
            
            # YAML frontmatter
            if include_metadata:
                formatted_doc += f"""---
title: "{title}"
author: "{author}"
date: "{datetime.now().strftime('%Y-%m-%d')}"
description: "Documento generato automaticamente"
keywords: []
tags: []
---

"""
            
            # Titolo principale
            formatted_doc += f"# {title}\n\n"
            
            # Informazioni documento
            formatted_doc += f"""**Autore:** {author}  
**Data:** {datetime.now().strftime('%d/%m/%Y')}  
**Ultima modifica:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

---

"""
            
            # Genera TOC se il contenuto ha headers
            if re.search(r'^#+\s', content, re.MULTILINE):
                headers = []
                for line in content.split('\n'):
                    stripped = line.strip()
                    if stripped.startswith('#'):
                        level = len(re.match(r'^#+', stripped).group())
                        if level <= 3:  # Max 3 livelli nel TOC
                            title_text = re.sub(r'^#+\s*', '', stripped)
                            anchor = re.sub(r'[^a-zA-Z0-9\s-]', '', title_text.lower())
                            anchor = re.sub(r'\s+', '-', anchor.strip())
                            headers.append((level, title_text, anchor))
                
                if headers:
                    formatted_doc += "## Indice\n\n"
                    for level, title_text, anchor in headers:
                        indent = "  " * (level - 1)
                        formatted_doc += f"{indent}- [{title_text}](#{anchor})\n"
                    formatted_doc += "\n---\n\n"
            
            # Contenuto principale
            formatted_doc += content
            
            # Footer
            formatted_doc += f"""

---

**Documento generato il:** {datetime.now().strftime('%d/%m/%Y alle %H:%M')}  
**Strumento:** Nexus MCP Server - Markdown Tools

*Questo documento è stato formattato automaticamente. Verificare la correttezza del contenuto.*"""
            
            # Statistiche documento
            word_count = len(re.findall(r'\b\w+\b', content))
            char_count = len(formatted_doc)
            header_count = len(re.findall(r'^#+\s', content, re.MULTILINE))
            
            return f"""📄 DOCUMENTO MARKDOWN FORMATTATO
Titolo: {title}
Autore: {author}
Parole: {word_count:,}
Caratteri: {char_count:,}
Headers: {header_count}
Metadata: {'Inclusi' if include_metadata else 'Esclusi'}

DOCUMENTO:
{formatted_doc}"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"