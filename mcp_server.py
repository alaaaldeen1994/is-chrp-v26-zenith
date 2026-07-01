import sys
import os
import json
import traceback

# Add SDK directory to python path to import ZenithClient
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sdks", "python"))

from zenith.client import ZenithClient
from zenith.exceptions import ZenithException

# Expose tools list matching MCP schema
TOOLS = [
    {
        "name": "safety_audit",
        "description": "Evaluates candidate transcription factors or biological compounds for oncogenic risks and calculates biological age from CpG methylation data.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "factors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of gene symbols (e.g. ['GATA4', 'TBX5', 'OCT4']) to evaluate."
                },
                "cpg_methylation": {
                    "type": "object",
                    "additionalProperties": {"type": "number"},
                    "description": "Optional mapping of CpG site probe IDs to their methylation beta-values."
                }
            },
            "required": ["factors"]
        }
    },
    {
        "name": "optimize_lnp",
        "description": "Simulates Lipid Nanoparticle (LNP) packaging formulations to optimize organ tropism, endosomal escape, and cytotoxicity.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "molar_ratios": {
                    "type": "object",
                    "properties": {
                        "ionizable": {"type": "number"},
                        "helper": {"type": "number"},
                        "cholesterol": {"type": "number"},
                        "peg": {"type": "number"}
                    },
                    "required": ["ionizable", "helper", "cholesterol", "peg"],
                    "description": "Molar percentages of lipids (must sum to 1.0/100%)."
                },
                "np_ratio": {
                    "type": "number",
                    "description": "Nitrogen-to-Phosphate molar ratio (usually between 1.0 and 20.0)."
                },
                "active_ligand_conjugation": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether active targeting ligands are conjugated to the surface."
                },
                "ligand_density": {
                    "type": "number",
                    "default": 0.0,
                    "description": "Percentage density of targeted surface ligands."
                },
                "peg_mw": {
                    "type": "number",
                    "default": 2000.0,
                    "description": "Molecular weight of PEG lipids in Da (usually 2000 Da)."
                }
            },
            "required": ["molar_ratios", "np_ratio"]
        }
    },
    {
        "name": "predict_perturbation",
        "description": "Queries live single-cell expression datasets and projects transcriptional drift under targeted perturbations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "perturbation_factors": {
                    "type": "object",
                    "additionalProperties": {"type": "number"},
                    "description": "Gene symbols and their dosage levels (e.g. {'GATA4': 1.5, 'SIRT1': 2.0})."
                },
                "baseline_cell_type": {
                    "type": "string",
                    "default": "ventricular_myocyte",
                    "description": "Baseline target cell type: ventricular_myocyte, fibroblast, etc."
                },
                "census_filter": {
                    "type": "string",
                    "description": "Optional Cellxgene Census dataset query filter."
                }
            },
            "required": ["perturbation_factors"]
        }
    },
    {
        "name": "fold_sequence",
        "description": "Folds an amino acid sequence using ESMFold, returning 3D atomic coordinates in standard PDB format.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sequence": {
                    "type": "string",
                    "description": "Amino acid letters representing the protein chain."
                }
            },
            "required": ["sequence"]
        }
    }
]

def log_debug(msg: str):
    """Write debug logs to stderr so they don't corrupt stdout JSON-RPC messaging."""
    sys.stderr.write(f"[DEBUG] {msg}\n")
    sys.stderr.flush()

class ZenithMCPServer:
    def __init__(self):
        # Read parameters from environment, default to Railway production API
        self.api_key = os.getenv("ZENITH_API_KEY")
        self.base_url = os.getenv("ZENITH_API_URL", "https://niluslab.com/api/v1")
        
        if not self.api_key:
            log_debug("WARNING: ZENITH_API_KEY environment variable is missing. Authentication calls will fail.")
        
        self.client = None
        if self.api_key:
            self.client = ZenithClient(api_key=self.api_key, base_url=self.base_url)

    def run(self):
        log_debug("Zenith MCP Server started. Listening on stdin...")
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                request = json.loads(line)
                self.handle_request(request)
            except Exception as e:
                log_debug(f"JSON-RPC parsing error: {e}")
                self.send_error(None, -32700, "Parse error")

    def handle_request(self, req: dict):
        req_id = req.get("id")
        method = req.get("method")
        
        # Check standard JSON-RPC 2.0 fields
        if req.get("jsonrpc") != "2.0":
            self.send_error(req_id, -32600, "Invalid Request")
            return
            
        log_debug(f"Handling method: {method}")
        
        if method == "initialize":
            self.send_result(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "zenith-mcp-server",
                    "version": "30.1.0"
                }
            })
        elif method == "tools/list":
            self.send_result(req_id, {
                "tools": TOOLS
            })
        elif method == "tools/call":
            params = req.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            self.execute_tool(req_id, tool_name, arguments)
        else:
            self.send_error(req_id, -32601, f"Method not found: {method}")

    def execute_tool(self, req_id: any, name: str, args: dict):
        if not self.client:
            self.send_error(req_id, -32000, "Authentication error: ZENITH_API_KEY is not set.")
            return

        try:
            if name == "safety_audit":
                res = self.client.safety_audit(
                    factors=args.get("factors", []),
                    cpg_methylation=args.get("cpg_methylation")
                )
            elif name == "optimize_lnp":
                res = self.client.optimize_lnp(
                    molar_ratios=args.get("molar_ratios", {}),
                    np_ratio=args.get("np_ratio", 6.0),
                    active_ligand_conjugation=args.get("active_ligand_conjugation", False),
                    ligand_density=args.get("ligand_density", 0.0),
                    peg_mw=args.get("peg_mw", 2000.0)
                )
            elif name == "predict_perturbation":
                # For MCP tools, we block and poll by default to return final calculations to LLMs
                res = self.client.predict_perturbation(
                    perturbation_factors=args.get("perturbation_factors", {}),
                    baseline_cell_type=args.get("baseline_cell_type", "ventricular_myocyte"),
                    census_filter=args.get("census_filter"),
                    poll=True
                )
            elif name == "fold_sequence":
                res = self.client.fold_sequence(sequence=args.get("sequence", ""))
            else:
                self.send_error(req_id, -32601, f"Tool not found: {name}")
                return

            # Construct MCP content format response
            self.send_result(req_id, {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(res, indent=2)
                    }
                ]
            })

        except ZenithException as e:
            self.send_error(req_id, -32001, f"Zenith API Exception: {e}")
        except Exception as e:
            log_debug(traceback.format_exc())
            self.send_error(req_id, -32603, f"Internal server error: {e}")

    def send_result(self, req_id: any, result: dict):
        response = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result
        }
        self.write_response(response)

    def send_error(self, req_id: any, code: int, message: str):
        response = {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        self.write_response(response)

    def write_response(self, response: dict):
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    server = ZenithMCPServer()
    server.run()
