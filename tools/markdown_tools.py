# -*- coding: utf-8 -*-
# tools/markdown_tools.py
import logging
import re
import os
import json
import tempfile
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
import urllib.parse

def register_tools(mcp):
    """Registra i tool Markdown avanzati con l'istanza del server MCP."""
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

    @mcp.tool()
    def validate_markdown_document(markdown_text: str, validation_rules: List[str] = None) -> Dict[str, Any]:
        """
        Valida un documento Markdown contro regole di qualità e best practices.
        
        Args:
            markdown_text: Testo Markdown da validare
            validation_rules: Regole specifiche da applicare
        """
        try:
            validation_rules = validation_rules or [
                "headers", "links", "images", "lists", "line_length", 
                "structure", "accessibility", "seo"
            ]
            
            validation_result = {
                "success": True,
                "document_valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": [],
                "metrics": {},
                "quality_score": 0
            }
            
            lines = markdown_text.split('\n')
            
            # Header validation
            if "headers" in validation_rules:
                header_issues = _validate_headers(lines)
                validation_result["errors"].extend(header_issues["errors"])
                validation_result["warnings"].extend(header_issues["warnings"])
                validation_result["metrics"]["header_structure"] = header_issues["metrics"]
            
            # Link validation
            if "links" in validation_rules:
                link_issues = _validate_links(markdown_text)
                validation_result["warnings"].extend(link_issues["warnings"])
                validation_result["metrics"]["links"] = link_issues["metrics"]
            
            # Image validation
            if "images" in validation_rules:
                image_issues = _validate_images(markdown_text)
                validation_result["warnings"].extend(image_issues["warnings"])
                validation_result["metrics"]["images"] = image_issues["metrics"]
            
            # List validation
            if "lists" in validation_rules:
                list_issues = _validate_lists(lines)
                validation_result["warnings"].extend(list_issues["warnings"])
                validation_result["metrics"]["lists"] = list_issues["metrics"]
            
            # Line length validation
            if "line_length" in validation_rules:
                line_issues = _validate_line_length(lines, max_length=100)
                validation_result["warnings"].extend(line_issues["warnings"])
                validation_result["metrics"]["line_length"] = line_issues["metrics"]
            
            # Document structure validation
            if "structure" in validation_rules:
                structure_issues = _validate_document_structure(markdown_text)
                validation_result["warnings"].extend(structure_issues["warnings"])
                validation_result["suggestions"].extend(structure_issues["suggestions"])
                validation_result["metrics"]["structure"] = structure_issues["metrics"]
            
            # Accessibility validation
            if "accessibility" in validation_rules:
                a11y_issues = _validate_accessibility(markdown_text)
                validation_result["warnings"].extend(a11y_issues["warnings"])
                validation_result["suggestions"].extend(a11y_issues["suggestions"])
            
            # SEO validation
            if "seo" in validation_rules:
                seo_issues = _validate_seo_elements(markdown_text)
                validation_result["suggestions"].extend(seo_issues["suggestions"])
                validation_result["metrics"]["seo"] = seo_issues["metrics"]
            
            # Calculate quality score
            validation_result["quality_score"] = _calculate_quality_score(validation_result)
            validation_result["document_valid"] = len(validation_result["errors"]) == 0
            
            return validation_result
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_markdown_template(template_type: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Genera template Markdown per diversi tipi di documenti.
        
        Args:
            template_type: Tipo template (article, readme, api_doc, blog_post, meeting_notes, proposal)
            options: Opzioni personalizzazione template
        """
        try:
            options = options or {}
            
            templates = {
                "article": _generate_article_template,
                "readme": _generate_readme_template,
                "api_doc": _generate_api_doc_template,
                "blog_post": _generate_blog_post_template,
                "meeting_notes": _generate_meeting_notes_template,
                "proposal": _generate_proposal_template,
                "technical_spec": _generate_technical_spec_template,
                "user_guide": _generate_user_guide_template
            }
            
            if template_type not in templates:
                return {
                    "success": False,
                    "error": f"Template type '{template_type}' not supported. Available: {', '.join(templates.keys())}"
                }
            
            template_content = templates[template_type](options)
            
            # Add metadata
            template_info = {
                "template_type": template_type,
                "generated_at": datetime.now().isoformat(),
                "options_used": options,
                "word_count": len(template_content.split()),
                "sections": len(re.findall(r'^#+\s', template_content, re.MULTILINE))
            }
            
            return {
                "success": True,
                "template_type": template_type,
                "template_content": template_content,
                "template_info": template_info,
                "next_steps": _get_template_next_steps(template_type)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def convert_markdown_to_formats(markdown_text: str, target_formats: List[str], 
                                   export_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Converte Markdown in multipli formati di output.
        
        Args:
            markdown_text: Testo Markdown da convertire
            target_formats: Formati target (html, pdf, docx, latex, plain_text)
            export_options: Opzioni specifiche per ogni formato
        """
        try:
            export_options = export_options or {}
            conversion_results = {}
            
            for fmt in target_formats:
                if fmt == "html":
                    result = _convert_to_html_advanced(markdown_text, export_options.get("html", {}))
                elif fmt == "latex":
                    result = _convert_to_latex(markdown_text, export_options.get("latex", {}))
                elif fmt == "plain_text":
                    result = _convert_to_plain_text(markdown_text, export_options.get("plain_text", {}))
                elif fmt == "json":
                    result = _convert_to_structured_json(markdown_text)
                elif fmt == "xml":
                    result = _convert_to_xml(markdown_text)
                else:
                    result = {"success": False, "error": f"Format '{fmt}' not supported"}
                
                conversion_results[fmt] = result
            
            # Generate export package
            export_package = _create_export_package(conversion_results, markdown_text)
            
            return {
                "success": True,
                "source_stats": {
                    "word_count": len(markdown_text.split()),
                    "char_count": len(markdown_text),
                    "line_count": len(markdown_text.split('\n'))
                },
                "conversions": conversion_results,
                "export_package": export_package,
                "formats_converted": len([fmt for fmt, result in conversion_results.items() if result.get("success")])
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def analyze_markdown_content(markdown_text: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Analisi approfondita contenuto Markdown per qualità e ottimizzazione.
        
        Args:
            markdown_text: Testo da analizzare
            analysis_type: Tipo analisi (comprehensive, readability, seo, structure)
        """
        try:
            analysis_result = {
                "analysis_type": analysis_type,
                "document_stats": _get_document_statistics(markdown_text),
                "metrics": {}
            }
            
            if analysis_type in ["comprehensive", "readability"]:
                # Readability analysis
                readability_metrics = _analyze_readability(markdown_text)
                analysis_result["metrics"]["readability"] = readability_metrics
            
            if analysis_type in ["comprehensive", "seo"]:
                # SEO analysis
                seo_metrics = _analyze_seo_content(markdown_text)
                analysis_result["metrics"]["seo"] = seo_metrics
            
            if analysis_type in ["comprehensive", "structure"]:
                # Structure analysis
                structure_metrics = _analyze_document_structure_detailed(markdown_text)
                analysis_result["metrics"]["structure"] = structure_metrics
            
            if analysis_type == "comprehensive":
                # Additional comprehensive analysis
                analysis_result["metrics"]["language"] = _analyze_language_patterns(markdown_text)
                analysis_result["metrics"]["content_density"] = _analyze_content_density(markdown_text)
                analysis_result["metrics"]["engagement"] = _analyze_engagement_factors(markdown_text)
            
            # Generate recommendations
            analysis_result["recommendations"] = _generate_content_recommendations(analysis_result["metrics"])
            
            # Calculate overall score
            analysis_result["overall_score"] = _calculate_content_score(analysis_result["metrics"])
            
            return analysis_result
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def create_markdown_presentation(markdown_text: str, presentation_type: str = "reveal_js") -> Dict[str, Any]:
        """
        Converte Markdown in presentazione interattiva.
        
        Args:
            markdown_text: Contenuto Markdown
            presentation_type: Tipo presentazione (reveal_js, deck_js, impress_js)
        """
        try:
            # Parse slides da headers
            slides = _parse_slides_from_markdown(markdown_text)
            
            if not slides:
                return {"success": False, "error": "No slides detected. Use ## headers to define slides."}
            
            if presentation_type == "reveal_js":
                presentation_html = _generate_reveal_js_presentation(slides, markdown_text)
            elif presentation_type == "deck_js":
                presentation_html = _generate_deck_js_presentation(slides, markdown_text)
            elif presentation_type == "impress_js":
                presentation_html = _generate_impress_js_presentation(slides, markdown_text)
            else:
                return {"success": False, "error": f"Presentation type '{presentation_type}' not supported"}
            
            # Save presentation
            temp_dir = tempfile.mkdtemp(prefix="nexus_presentation_")
            presentation_file = os.path.join(temp_dir, f"presentation_{presentation_type}.html")
            
            with open(presentation_file, 'w', encoding='utf-8') as f:
                f.write(presentation_html)
            
            return {
                "success": True,
                "presentation_type": presentation_type,
                "slides_count": len(slides),
                "presentation_file": presentation_file,
                "slides_preview": [{"title": slide.get("title", "Untitled"), "content_length": len(slide.get("content", ""))} for slide in slides[:5]],
                "presentation_stats": {
                    "total_slides": len(slides),
                    "estimated_duration_minutes": len(slides) * 2,  # 2 min per slide
                    "file_size_kb": round(len(presentation_html) / 1024, 2)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_markdown_documentation(project_info: Dict[str, Any], 
                                      doc_types: List[str] = None) -> Dict[str, Any]:
        """
        Genera documentazione completa progetto in Markdown.
        
        Args:
            project_info: Informazioni progetto (name, description, version, etc.)
            doc_types: Tipi documentazione da generare
        """
        try:
            doc_types = doc_types or ["readme", "changelog", "contributing", "api", "user_guide"]
            
            generated_docs = {}
            
            for doc_type in doc_types:
                if doc_type == "readme":
                    content = _generate_project_readme(project_info)
                elif doc_type == "changelog":
                    content = _generate_changelog_template(project_info)
                elif doc_type == "contributing":
                    content = _generate_contributing_guide(project_info)
                elif doc_type == "api":
                    content = _generate_api_documentation(project_info)
                elif doc_type == "user_guide":
                    content = _generate_user_guide_template(project_info)
                elif doc_type == "installation":
                    content = _generate_installation_guide(project_info)
                elif doc_type == "troubleshooting":
                    content = _generate_troubleshooting_guide(project_info)
                else:
                    content = f"# {doc_type.title()}\n\nTODO: Add {doc_type} documentation."
                
                generated_docs[doc_type] = {
                    "content": content,
                    "filename": f"{doc_type.upper()}.md",
                    "word_count": len(content.split()),
                    "sections": len(re.findall(r'^#+\s', content, re.MULTILINE))
                }
            
            # Create documentation package
            docs_package = _create_documentation_package(generated_docs, project_info)
            
            return {
                "success": True,
                "project_name": project_info.get("name", "Unknown Project"),
                "docs_generated": list(generated_docs.keys()),
                "total_docs": len(generated_docs),
                "documentation": generated_docs,
                "package_info": docs_package,
                "next_steps": [
                    "Review and customize generated documentation",
                    "Add project-specific details",
                    "Update examples and code snippets",
                    "Add screenshots and diagrams where needed",
                    "Set up documentation hosting (GitHub Pages, etc.)"
                ]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def batch_process_markdown_files(file_operations: List[Dict[str, Any]], 
                                   operation_type: str) -> Dict[str, Any]:
        """
        Elaborazione batch di file Markdown multipli.
        
        Args:
            file_operations: Lista operazioni file (file_path, content, options)
            operation_type: Tipo operazione (validate, convert, analyze, format)
        """
        try:
            if len(file_operations) > 20:
                return {"success": False, "error": "Too many files (max 20)"}
            
            results = []
            successful_operations = 0
            
            for i, operation in enumerate(file_operations):
                file_name = operation.get("name", f"file_{i+1}")
                content = operation.get("content", "")
                options = operation.get("options", {})
                
                operation_result = {
                    "file_name": file_name,
                    "operation_type": operation_type,
                    "success": False
                }
                
                try:
                    if operation_type == "validate":
                        result = validate_markdown_document(content, options.get("validation_rules"))
                        operation_result.update(result)
                        operation_result["success"] = result.get("success", False)
                    
                    elif operation_type == "convert":
                        target_formats = options.get("target_formats", ["html"])
                        result = convert_markdown_to_formats(content, target_formats, options.get("export_options"))
                        operation_result.update(result)
                        operation_result["success"] = result.get("success", False)
                    
                    elif operation_type == "analyze":
                        analysis_type = options.get("analysis_type", "comprehensive")
                        result = analyze_markdown_content(content, analysis_type)
                        operation_result.update(result)
                        operation_result["success"] = True
                    
                    elif operation_type == "format":
                        title = options.get("title", file_name)
                        author = options.get("author", "Unknown")
                        include_metadata = options.get("include_metadata", True)
                        result = format_markdown_document(title, author, content, include_metadata)
                        operation_result["formatted_content"] = result
                        operation_result["success"] = True
                    
                    else:
                        operation_result["error"] = f"Unknown operation type: {operation_type}"
                    
                    if operation_result["success"]:
                        successful_operations += 1
                        
                except Exception as e:
                    operation_result["error"] = str(e)
                
                results.append(operation_result)
            
            return {
                "success": True,
                "operation_type": operation_type,
                "total_files": len(file_operations),
                "successful_operations": successful_operations,
                "failed_operations": len(file_operations) - successful_operations,
                "success_rate": round((successful_operations / len(file_operations)) * 100, 1),
                "results": results
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Enhanced helper functions
    def _validate_headers(lines: List[str]) -> Dict[str, Any]:
        """Valida struttura header."""
        errors = []
        warnings = []
        header_levels = []
        
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('#'):
                level = len(re.match(r'^#+', line.strip()).group())
                header_levels.append((i, level, line.strip()))
                
                # Check for proper spacing
                if not re.match(r'^#+\s+\S', line.strip()):
                    errors.append(f"Line {i}: Header missing space after #")
                
                # Check for empty headers
                title = re.sub(r'^#+\s*', '', line.strip())
                if not title:
                    errors.append(f"Line {i}: Empty header")
        
        # Check header hierarchy
        for i in range(1, len(header_levels)):
            prev_level = header_levels[i-1][1]
            curr_level = header_levels[i][1]
            
            if curr_level > prev_level + 1:
                warnings.append(f"Line {header_levels[i][0]}: Header level jumps from H{prev_level} to H{curr_level}")
        
        return {
            "errors": errors,
            "warnings": warnings,
            "metrics": {
                "total_headers": len(header_levels),
                "max_level": max([h[1] for h in header_levels]) if header_levels else 0,
                "hierarchy_violations": len([w for w in warnings if "level jumps" in w])
            }
        }

    def _generate_article_template(options: Dict[str, Any]) -> str:
        """Genera template per articolo."""
        title = options.get("title", "Article Title")
        author = options.get("author", "Author Name")
        date = datetime.now().strftime("%Y-%m-%d")
        
        return f"""---
title: "{title}"
author: "{author}"
date: {date}
tags: []
categories: []
---

# {title}

## Introduction

Write your introduction here. Explain what this article covers and why it's important.

## Main Content

### Section 1

Add your main content here.

### Section 2

Continue with additional sections as needed.

## Key Points

- Important point 1
- Important point 2
- Important point 3

## Conclusion

Summarize your main points and provide next steps or call to action.

## References

1. Reference 1
2. Reference 2
3. Reference 3

---

*Article by {author} - {date}*
"""

    def _generate_readme_template(options: Dict[str, Any]) -> str:
        """Genera template README per progetto."""
        project_name = options.get("project_name", "Project Name")
        description = options.get("description", "Brief project description")
        
        return f"""# {project_name}

{description}

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Contributing](#contributing)
- [License](#license)

## Installation

```bash
# Installation instructions
npm install {project_name.lower().replace(' ', '-')}
```

## Usage

```javascript
// Basic usage example
const {project_name.lower().replace(' ', '')} = require('{project_name.lower().replace(' ', '-')}');

// Your code here
```

## Features

- ✨ Feature 1
- 🚀 Feature 2
- 🔧 Feature 3

## API Documentation

### Method 1

Description of method 1.

```javascript
// Example usage
```

### Method 2

Description of method 2.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you have any questions or need help, please:

- Check the [Issues](../../issues) page
- Contact us at [email]

---

Made with ❤️ by [Your Name]
"""

    def _convert_to_html_advanced(markdown_text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Conversione HTML avanzata con CSS e JavaScript."""
        try:
            # Use existing HTML conversion as base
            html_content = markdown_to_html(markdown_text)
            
            # Extract just the HTML part
            html_body = html_content.split("HTML GENERATO:\n")[1].split("\n\n💡 NOTA:")[0]
            
            # Add advanced features
            include_css = options.get("include_css", True)
            include_js = options.get("include_js", False)
            theme = options.get("theme", "default")
            
            full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown Document</title>
    {_get_html_css(theme) if include_css else ''}
    {_get_html_js() if include_js else ''}
</head>
<body>
    <div class="markdown-content">
        {html_body}
    </div>
</body>
</html>"""
            
            return {
                "success": True,
                "content": full_html,
                "size_bytes": len(full_html),
                "features": {
                    "css_included": include_css,
                    "js_included": include_js,
                    "theme": theme
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_html_css(theme: str) -> str:
        """Ottieni CSS per tema HTML."""
        themes = {
            "default": """
    <style>
        .markdown-content { max-width: 800px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif; }
        h1, h2, h3, h4, h5, h6 { color: #333; }
        code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
        pre { background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }
        blockquote { border-left: 4px solid #ddd; margin-left: 0; padding-left: 16px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>""",
            "dark": """
    <style>
        body { background-color: #1a1a1a; color: #e0e0e0; }
        .markdown-content { max-width: 800px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif; }
        h1, h2, h3, h4, h5, h6 { color: #ffffff; }
        code { background: #2d2d2d; padding: 2px 4px; border-radius: 3px; color: #ff6b6b; }
        pre { background: #2d2d2d; padding: 10px; border-radius: 5px; overflow-x: auto; }
        blockquote { border-left: 4px solid #555; margin-left: 0; padding-left: 16px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #555; padding: 8px; text-align: left; }
        th { background-color: #333; }
        a { color: #4dabf7; }
    </style>"""
        }
        return themes.get(theme, themes["default"])