import re
from pathlib import Path
from typing import Optional, List, Dict, Any

from convert_id.engines.base import BaseEngine, ConversionResult

class CodeEngine(BaseEngine):
    name = "CodeEngine"
    supported_inputs = ["svg", "json"]
    supported_outputs = ["tsx", "jsx", "vue", "dart", "ts"]

    def convert(self, input_path: Path, output_path: Path, **kwargs) -> ConversionResult:
        input_path = Path(input_path)
        output_path = Path(output_path)
        orig_size = input_path.stat().st_size if input_path.exists() else 0
        in_ext = input_path.suffix.lstrip(".").lower()
        out_ext = output_path.suffix.lstrip(".").lower()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        component_name = kwargs.get("component_name") or self._to_pascal_case(input_path.stem)

        if in_ext == "svg":
            svg_content = input_path.read_text(encoding="utf-8")
            
            # Anti-mainstream #11: SVG to React TSX / JSX
            if out_ext in ["tsx", "jsx"]:
                code = self._svg_to_react(svg_content, component_name, is_typescript=(out_ext == "tsx"))
            # SVG to Vue 3
            elif out_ext == "vue":
                code = self._svg_to_vue(svg_content, component_name)
            # SVG to Flutter Dart
            elif out_ext == "dart":
                code = self._svg_to_flutter(svg_content, component_name)
            else:
                code = svg_content

            output_path.write_text(code, encoding="utf-8")
            new_sz = output_path.stat().st_size
            return ConversionResult(
                success=True,
                output_path=output_path,
                original_size=orig_size,
                converted_size=new_sz,
                format_from=in_ext,
                format_to=out_ext,
                message=f"Generated {out_ext.upper()} component '{component_name}'."
            )

        return ConversionResult(
            success=False,
            output_path=None,
            original_size=orig_size,
            converted_size=0,
            format_from=in_ext,
            format_to=out_ext,
            message="Unsupported code generation path."
        )

    def _to_pascal_case(self, s: str) -> str:
        words = re.findall(r'[A-Za-z0-9]+', s)
        return "".join(w.capitalize() for w in words) or "IconComponent"

    def _svg_to_react(self, svg: str, name: str, is_typescript: bool = True) -> str:
        # Replace kebab-case attributes with camelCase
        svg_clean = re.sub(r'xmlns(:\w+)?="[^"]*"', '', svg)
        svg_clean = re.sub(r'<\?xml[^>]*\?>', '', svg_clean)
        
        # Replace attribute names
        for attr in ["fill-rule", "clip-rule", "stroke-width", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit"]:
            camel = "".join(p.capitalize() if i > 0 else p for i, p in enumerate(attr.split("-")))
            svg_clean = svg_clean.replace(f'{attr}=', f'{camel}=')

        svg_clean = svg_clean.strip()
        
        # Inject {...props} into root svg tag
        svg_clean = re.sub(r'<svg', r'<svg {...props}', svg_clean, count=1)

        if is_typescript:
            return f'''import React from "react";

export interface {name}Props extends React.SVGProps<SVGSVGElement> {{
  size?: number | string;
}}

export const {name}: React.FC<{name}Props> = ({{ size = 24, ...props }}) => (
  {svg_clean}
);

export default {name};
'''
        else:
            return f'''import React from "react";

export const {name} = ({{ size = 24, ...props }}) => (
  {svg_clean}
);

export default {name};
'''

    def _svg_to_vue(self, svg: str, name: str) -> str:
        svg_clean = re.sub(r'<\?xml[^>]*\?>', '', svg).strip()
        return f'''<template>
  {svg_clean}
</template>

<script setup>
defineProps({{
  size: {{
    type: [Number, String],
    default: 24
  }}
}});
</script>
'''

    def _svg_to_flutter(self, svg: str, name: str) -> str:
        return f'''import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class {name} extends StatelessWidget {{
  final double size;
  final Color? color;

  const {name}({{super.key, this.size = 24.0, this.color}});

  @override
  Widget build(BuildContext context) {{
    const String rawSvg = \'\'\'{svg}\'\'\';
    return SvgPicture.string(
      rawSvg,
      width: size,
      height: size,
      colorFilter: color != null ? ColorFilter.mode(color!, BlendMode.srcIn) : null,
    );
  }}
}}
'''
