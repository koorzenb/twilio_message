"""Email template engine for IRCC notifications."""

import os
import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class TemplateEngine:
    """
    Simple template engine for email notifications.
    
    Supports basic variable substitution and conditional blocks
    using mustache-like syntax ({{variable}} and {{#condition}}).
    """
    
    def __init__(self, template_dir: str = "templates"):
        """
        Initialize template engine.
        
        Args:
            template_dir: Directory containing template files
        """
        self.template_dir = Path(__file__).parent / template_dir
        if not self.template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {self.template_dir}")
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context.
        
        Args:
            template_name: Name of the template file
            context: Dictionary of variables to substitute
            
        Returns:
            str: Rendered template content
            
        Raises:
            FileNotFoundError: If template file doesn't exist
            ValueError: If template rendering fails
        """
        template_path = self.template_dir / template_name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Process the template
            rendered = self._process_template(template_content, context)
            
            logger.info(f"Successfully rendered template: {template_name}")
            return rendered
            
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise ValueError(f"Template rendering failed: {e}")
    
    def _process_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Process template with variable substitution and conditional blocks.
        
        Args:
            template: Template content
            context: Context variables
            
        Returns:
            str: Processed template
        """
        # First, process conditional blocks
        template = self._process_conditional_blocks(template, context)
        
        # Then, substitute simple variables
        template = self._substitute_variables(template, context)
        
        return template
    
    def _process_conditional_blocks(self, template: str, context: Dict[str, Any]) -> str:
        """
        Process conditional blocks like {{#condition}}...{{/condition}}.
        
        Args:
            template: Template content
            context: Context variables
            
        Returns:
            str: Template with conditional blocks processed
        """
        # Pattern for conditional blocks: {{#var}}content{{/var}}
        pattern = r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}'
        
        def replace_conditional(match):
            var_name = match.group(1)
            content = match.group(2)
            
            # Check if condition is true
            if var_name in context and self._is_truthy(context[var_name]):
                # Process nested variables in the conditional content
                return self._substitute_variables(content, context)
            else:
                return ''
        
        # Process conditional blocks (may be nested, so repeat until no more matches)
        while re.search(pattern, template, re.DOTALL):
            template = re.sub(pattern, replace_conditional, template, flags=re.DOTALL)
        
        # Process inverted conditionals: {{^var}}content{{/var}}
        pattern_inverted = r'\{\{\^(\w+)\}\}(.*?)\{\{/\1\}\}'
        
        def replace_inverted_conditional(match):
            var_name = match.group(1)
            content = match.group(2)
            
            # Check if condition is false
            if var_name not in context or not self._is_truthy(context[var_name]):
                return self._substitute_variables(content, context)
            else:
                return ''
        
        while re.search(pattern_inverted, template, re.DOTALL):
            template = re.sub(pattern_inverted, replace_inverted_conditional, template, flags=re.DOTALL)
        
        return template
    
    def _substitute_variables(self, template: str, context: Dict[str, Any]) -> str:
        """
        Substitute simple variables like {{variable}}.
        
        Args:
            template: Template content
            context: Context variables
            
        Returns:
            str: Template with variables substituted
        """
        # Pattern for simple variables: {{variable}}
        pattern = r'\{\{(\w+)\}\}'
        
        def replace_variable(match):
            var_name = match.group(1)
            if var_name in context:
                return str(context[var_name])
            else:
                logger.warning(f"Template variable not found: {var_name}")
                return f"{{{{MISSING: {var_name}}}}}"
        
        return re.sub(pattern, replace_variable, template)
    
    def _is_truthy(self, value: Any) -> bool:
        """
        Check if a value is truthy for template conditionals.
        
        Args:
            value: Value to check
            
        Returns:
            bool: True if value is truthy
        """
        if isinstance(value, bool):
            return value
        elif isinstance(value, (list, dict, str)):
            return len(value) > 0
        elif value is None:
            return False
        else:
            return bool(value)


class IRCCEmailTemplateRenderer:
    """
    Specialized template renderer for IRCC email notifications.
    
    Provides high-level methods for rendering IRCC-specific email templates
    with proper context preparation and formatting.
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize IRCC template renderer.
        
        Args:
            template_dir: Optional custom template directory
        """
        if template_dir:
            self.engine = TemplateEngine(template_dir)
        else:
            # Use default template directory relative to src directory
            src_dir = Path(__file__).parent.parent
            template_path = src_dir / "templates"
            self.engine = TemplateEngine(str(template_path))
    
    def render_update_notification(
        self, 
        scraped_data: Dict[str, Any], 
        has_updates: bool,
        recent_history: Optional[List[Dict[str, Any]]] = None,
        format_type: str = "html"
    ) -> str:
        """
        Render an IRCC update notification email.
        
        Args:
            scraped_data: Data scraped from the IRCC website
            has_updates: Whether updates were detected
            recent_history: Optional recent change history
            format_type: Email format ('html' or 'text')
            
        Returns:
            str: Rendered email content
        """
        # Prepare context
        context = self._prepare_notification_context(scraped_data, has_updates, recent_history)
        
        # Select template
        if format_type == "text":
            template_name = "ircc_update_template.txt"
        else:
            template_name = f"ircc_update_template.{format_type}"
        
        return self.engine.render_template(template_name, context)
    
    def _prepare_notification_context(
        self, 
        scraped_data: Dict[str, Any], 
        has_updates: bool,
        recent_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Prepare template context from scraped data.
        
        Args:
            scraped_data: Raw scraped data
            has_updates: Whether updates were detected
            recent_history: Optional change history
            
        Returns:
            Dict[str, Any]: Template context
        """
        # Get current timestamp
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Extract basic data with safe defaults
        page_title = scraped_data.get('title', 'N/A')
        target_content = scraped_data.get('target_content', 'N/A')
        last_updated = scraped_data.get('last_updated', 'N/A')
        page_size = scraped_data.get('page_size', 0)
        notices = scraped_data.get('important_notices', [])
        website_url = scraped_data.get('url', 'https://www.canada.ca')
        
        # Determine status information
        if has_updates:
            status_class = "updated"
            status_text = "UPDATE DETECTED"
            update_highlight_class = "success"
            header_class = "update-detected"
        elif scraped_data is None:
            status_class = "error"
            status_text = "SCRAPING ERROR"
            update_highlight_class = "error"
            header_class = "error"
        else:
            status_class = "no-update"
            status_text = "NO UPDATES"
            update_highlight_class = ""
            header_class = "no-update"
        
        # Prepare context dictionary
        context = {
            # Status information
            'has_updates': has_updates,
            'status_class': status_class,
            'status_text': status_text,
            'update_highlight_class': update_highlight_class,
            'header_class': header_class,
            'timestamp': timestamp,
            
            # Website data
            'website_url': website_url,
            'website_title': 'Sponsor your parents and grandparents',
            'page_title': page_title,
            'target_content': target_content,
            'last_updated': last_updated,
            'page_size': f"{page_size:,}",
            
            # Notices
            'notices': notices,
            'notices_count': len(notices),
            'has_notices': len(notices) > 0,
            
            # History
            'show_history': has_updates,
            'history_available': recent_history is not None and len(recent_history) > 0,
            'recent_history': recent_history or [],
        }
        
        # Format history entries if available
        if recent_history:
            formatted_history = []
            for entry in recent_history[-5:]:  # Show last 5 entries
                content_hash = entry.get('target_content_hash', 'Unknown')
                if len(content_hash) > 8 and content_hash != 'Unknown':
                    content_hash = content_hash[:8] + '...'
                
                formatted_entry = {
                    'timestamp': entry.get('timestamp', 'Unknown'),
                    'change_reason': entry.get('change_reason', 'Unknown'),
                    'content_hash': content_hash,
                }
                formatted_history.append(formatted_entry)
            context['recent_history'] = formatted_history
        
        return context


# Convenience functions for easy usage
def render_ircc_html_email(
    scraped_data: Dict[str, Any], 
    has_updates: bool,
    recent_history: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Convenience function to render HTML email for IRCC notifications.
    
    Args:
        scraped_data: Data scraped from the IRCC website
        has_updates: Whether updates were detected
        recent_history: Optional recent change history
        
    Returns:
        str: HTML email content
    """
    renderer = IRCCEmailTemplateRenderer()
    return renderer.render_update_notification(scraped_data, has_updates, recent_history, "html")


def render_ircc_text_email(
    scraped_data: Dict[str, Any], 
    has_updates: bool,
    recent_history: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Convenience function to render text email for IRCC notifications.
    
    Args:
        scraped_data: Data scraped from the IRCC website
        has_updates: Whether updates were detected
        recent_history: Optional recent change history
        
    Returns:
        str: Plain text email content
    """
    renderer = IRCCEmailTemplateRenderer()
    return renderer.render_update_notification(scraped_data, has_updates, recent_history, "text")


if __name__ == "__main__":
    """Test the template engine when run as a standalone script."""
    import json
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Sample test data
    test_scraped_data = {
        'url': 'https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/family-sponsorship/sponsor-parents-grandparents.html',
        'title': 'Sponsor your parents and grandparents - Canada.ca',
        'target_content': 'Date modified: 2025-10-27',
        'last_updated': '2025-10-27',
        'page_size': 45678,
        'important_notices': [
            'Important: The 2024 Parent and Grandparent Program intake is now closed.',
            'New applications will not be accepted until further notice.'
        ],
        'scraped_at': '2025-10-27T15:30:00'
    }
    
    test_history = [
        {
            'timestamp': '2025-10-26T10:15:00',
            'change_reason': 'Target content changed',
            'target_content_hash': 'abc123def456'
        },
        {
            'timestamp': '2025-10-27T15:30:00',
            'change_reason': 'Important notices changed',
            'target_content_hash': 'def456ghi789'
        }
    ]
    
    try:
        print("Testing IRCC email template rendering...")
        
        # Test HTML template
        print("\n📧 Testing HTML template...")
        html_content = render_ircc_html_email(test_scraped_data, True, test_history)
        print(f"✅ HTML template rendered successfully ({len(html_content)} characters)")
        
        # Test text template
        print("\n📧 Testing text template...")
        text_content = render_ircc_text_email(test_scraped_data, True, test_history)
        print(f"✅ Text template rendered successfully ({len(text_content)} characters)")
        
        # Test no-updates scenario
        print("\n📧 Testing no-updates scenario...")
        no_update_html = render_ircc_html_email(test_scraped_data, False)
        print(f"✅ No-updates template rendered successfully ({len(no_update_html)} characters)")
        
        print("\n🎉 All template tests passed!")
        
        # Optionally save test outputs
        save_test = input("\nSave test outputs to files? (y/n): ").lower().startswith('y')
        if save_test:
            test_dir = Path(__file__).parent / "test_output"
            test_dir.mkdir(exist_ok=True)
            
            with open(test_dir / "test_email.html", 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            with open(test_dir / "test_email.txt", 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            print(f"✅ Test outputs saved to {test_dir}")
        
    except Exception as e:
        print(f"❌ Template test failed: {e}")
        import traceback
        traceback.print_exc()