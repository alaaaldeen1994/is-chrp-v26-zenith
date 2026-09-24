import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
script_path = os.path.join(base, 'js', 'script.js')

with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print(f"Total lines in js/script.js: {len(lines)}")

# Let's inspect lines 4790 to 4805
for i in range(4790, min(4805, len(lines))):
    print(f"Line {i+1}: {repr(lines[i])}")

# Let's check lines 4795 to 4802
# Line 4797 is '            }\n' before '        } catch (e) {\n'
# Replacing lines 4797-4801 with proper closing brace

old_sub = """                    svg.appendChild(group);
                });
            }
        } catch (e) {
            console.error("GraphRAG query request failed:", e);
        }
    },"""

new_sub = """                    svg.appendChild(group);
                });
            }
        } catch (e) {
            console.error("GraphRAG query request failed:", e);
        }
    },"""

# Let's check why Node complained:
# In renderGraphRAG:
# try {  <-- line 4273
#   try { <-- line 4275
#   } catch(fetchErr) { ... } <-- line 4288
#   ...
#   nodes.forEach(node => {
#      ...
#   }); <-- line 4796
# } <-- line 4797 (closes try line 4273)
# } catch(e) { <-- line 4798 (catch without matching try!)

# The outer try was at 4273, but line 4797 closed it BEFORE line 4798 catch(e)!
# Removing line 4797 '            }\n' fixes the syntax error!

content = "".join(lines)

bad_snippet = """                    svg.appendChild(group);
                });
            }
        } catch (e) {"""

fixed_snippet = """                    svg.appendChild(group);
                });
        } catch (e) {"""

if bad_snippet in content:
    content = content.replace(bad_snippet, fixed_snippet)
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Removed extra brace in js/script.js!")
else:
    print("Snippet not found, checking exact lines around 4795-4800...")

# Run Node syntax check
res = subprocess.run(['node', '-c', script_path], capture_output=True, text=True)
print("Node syntax check exit code:", res.returncode)
if res.returncode != 0:
    print("Stderr:", res.stderr)
else:
    print("🎉 SYNTAX PERFECT! No syntax errors in js/script.js!")
