import json
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import yaml
import toml
import pandas as pd

from convert_id.engines.base import BaseEngine, ConversionResult

class DataEngine(BaseEngine):
    name = "DataEngine"
    supported_inputs = ["json", "yaml", "yml", "toml", "xml", "csv", "tsv", "xlsx", "xls", "parquet"]
    supported_outputs = ["json", "yaml", "yml", "toml", "xml", "csv", "tsv", "sql", "xlsx", "parquet"]

    def convert(self, input_path: Path, output_path: Path, **kwargs) -> ConversionResult:
        input_path = Path(input_path)
        output_path = Path(output_path)
        orig_size = input_path.stat().st_size if input_path.exists() else 0
        in_ext = input_path.suffix.lstrip(".").lower()
        out_ext = output_path.suffix.lstrip(".").lower()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Tabular / Dataframe path
            if in_ext in ["csv", "tsv", "xlsx", "xls", "parquet"] or out_ext in ["sql", "xlsx", "parquet"]:
                return self._handle_tabular(input_path, output_path, in_ext, out_ext, orig_size, **kwargs)

            # 2. Hierarchical structure path (JSON, YAML, TOML, XML)
            data = self._read_hierarchical(input_path, in_ext)
            self._write_hierarchical(data, output_path, out_ext)

            new_sz = output_path.stat().st_size
            return ConversionResult(
                success=True,
                output_path=output_path,
                original_size=orig_size,
                converted_size=new_sz,
                format_from=in_ext,
                format_to=out_ext,
                message=f"Converted {in_ext.upper()} structure to {out_ext.upper()}."
            )

        except Exception as e:
            return ConversionResult(
                success=False,
                output_path=None,
                original_size=orig_size,
                converted_size=0,
                format_from=in_ext,
                format_to=out_ext,
                message=f"Data conversion failed: {str(e)}"
            )

    def _read_hierarchical(self, path: Path, ext: str) -> Any:
        content = path.read_text(encoding="utf-8")
        if ext == "json":
            return json.loads(content)
        elif ext in ["yaml", "yml"]:
            return yaml.safe_load(content)
        elif ext == "toml":
            return toml.loads(content)
        elif ext == "xml":
            root = ET.fromstring(content)
            return self._xml_to_dict(root)
        raise ValueError(f"Unsupported reader format: {ext}")

    def _write_hierarchical(self, data: Any, path: Path, ext: str):
        if ext == "json":
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        elif ext in ["yaml", "yml"]:
            path.write_text(yaml.dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
        elif ext == "toml":
            if isinstance(data, dict):
                path.write_text(toml.dumps(data), encoding="utf-8")
            else:
                path.write_text(toml.dumps({"data": data}), encoding="utf-8")
        elif ext == "xml":
            root = ET.Element("root")
            self._dict_to_xml(data, root)
            tree = ET.ElementTree(root)
            tree.write(str(path), encoding="utf-8", xml_declaration=True)

    def _handle_tabular(self, input_path: Path, output_path: Path, in_ext: str, out_ext: str, orig_size: int, **kwargs) -> ConversionResult:
        # Load into Pandas DataFrame
        if in_ext == "csv":
            df = pd.read_csv(input_path)
        elif in_ext == "tsv":
            df = pd.read_csv(input_path, sep="\t")
        elif in_ext in ["xlsx", "xls"]:
            df = pd.read_excel(input_path)
        elif in_ext == "parquet":
            df = pd.read_parquet(input_path)
        elif in_ext == "json":
            df = pd.read_json(input_path)
        else:
            raise ValueError(f"Cannot load {in_ext} as tabular dataset.")

        # Anti-mainstream #8: Auto-generate SQL DDL & INSERT statements
        if out_ext == "sql":
            table_name = kwargs.get("table_name", input_path.stem)
            sql_statements = self._df_to_sql(df, table_name)
            output_path.write_text(sql_statements, encoding="utf-8")
        elif out_ext == "csv":
            df.to_csv(output_path, index=False)
        elif out_ext == "tsv":
            df.to_csv(output_path, sep="\t", index=False)
        elif out_ext == "xlsx":
            df.to_excel(output_path, index=False)
        elif out_ext == "parquet":
            df.to_parquet(output_path, index=False)
        elif out_ext == "json":
            df.to_json(output_path, orient="records", indent=2)

        new_sz = output_path.stat().st_size
        return ConversionResult(
            success=True,
            output_path=output_path,
            original_size=orig_size,
            converted_size=new_sz,
            format_from=in_ext,
            format_to=out_ext,
            message=f"Tabular transformation successful ({len(df)} rows)."
        )

    def _df_to_sql(self, df: pd.DataFrame, table_name: str) -> str:
        """Generates CREATE TABLE and batch INSERT statements."""
        col_types = []
        for col, dtype in zip(df.columns, df.dtypes):
            clean_col = f"`{col}`"
            if "int" in str(dtype):
                sql_type = "BIGINT"
            elif "float" in str(dtype):
                sql_type = "DOUBLE"
            elif "bool" in str(dtype):
                sql_type = "BOOLEAN"
            elif "datetime" in str(dtype):
                sql_type = "DATETIME"
            else:
                sql_type = "VARCHAR(255)"
            col_types.append(f"  {clean_col} {sql_type}")

        ddl = f"CREATE TABLE IF NOT EXISTS `{table_name}` (\n" + ",\n".join(col_types) + "\n);\n\n"

        # Batch inserts
        inserts = []
        cols_joined = ", ".join(f"`{c}`" for c in df.columns)
        for _, row in df.iterrows():
            vals = []
            for v in row:
                if pd.isna(v):
                    vals.append("NULL")
                elif isinstance(v, (int, float)):
                    vals.append(str(v))
                elif isinstance(v, bool):
                    vals.append("TRUE" if v else "FALSE")
                else:
                    escaped = str(v).replace("'", "''")
                    vals.append(f"'{escaped}'")
            inserts.append(f"INSERT INTO `{table_name}` ({cols_joined}) VALUES ({', '.join(vals)});")

        return ddl + "\n".join(inserts)

    def _xml_to_dict(self, element: ET.Element) -> Union[Dict, str]:
        children = list(element)
        if not children:
            return element.text or ""
        result = {}
        for child in children:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        return result

    def _dict_to_xml(self, data: Any, parent: ET.Element):
        if isinstance(data, dict):
            for k, v in data.items():
                child = ET.SubElement(parent, str(k))
                self._dict_to_xml(v, child)
        elif isinstance(data, list):
            for item in data:
                child = ET.SubElement(parent, "item")
                self._dict_to_xml(item, child)
        else:
            parent.text = str(data)
