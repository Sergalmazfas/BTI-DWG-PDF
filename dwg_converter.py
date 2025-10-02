"""
DWG → PDF Converter
Local conversion using ezdxf + matplotlib
"""

import os
import logging
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import ezdxf
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    import matplotlib.pyplot as plt
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    logger.warning(f"DWG→PDF dependencies not available: {e}")


def convert_dwg_to_pdf(dwg_path: str) -> Optional[str]:
    """
    Convert DWG to PDF locally using ezdxf + matplotlib
    
    Args:
        dwg_path: Path to DWG file
        
    Returns:
        Path to generated PDF file, or None if failed
    """
    if not DEPENDENCIES_AVAILABLE:
        logger.error("❌ DWG→PDF: Dependencies not available (ezdxf, matplotlib)")
        return None
    
    try:
        logger.info(f"🔄 DWG→PDF: Converting {dwg_path} locally...")
        
        # Read DWG file
        doc = ezdxf.readfile(dwg_path)
        msp = doc.modelspace()
        
        logger.info(f"✅ DWG file loaded: {doc.dxfversion}")
        
        # Create PDF output path
        pdf_path = dwg_path.replace('.dwg', '.pdf').replace('.DWG', '.pdf')
        if pdf_path == dwg_path:
            pdf_path = dwg_path + '.pdf'
        
        # Render using matplotlib backend
        fig = plt.figure(figsize=(11.69, 8.27))  # A4 landscape in inches
        ax = fig.add_axes([0, 0, 1, 1])
        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)
        
        # Render all entities
        Frontend(ctx, out).draw_layout(msp, finalize=True)
        
        # Save as PDF
        fig.savefig(pdf_path, format='pdf', dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"✅ DWG→PDF: Local conversion successful: {pdf_path}")
        
        return pdf_path
        
    except Exception as e:
        logger.error(f"❌ DWG→PDF: Local conversion failed: {e}")
        return None


def convert_dwg_to_pdf_simple(dwg_path: str) -> Optional[str]:
    """
    Simple DWG → PDF: Just save DWG as-is and return message
    This is a fallback when matplotlib is not available
    """
    logger.warning("⚠️ DWG→PDF: PDF conversion not available, DWG saved as-is")
    return None
