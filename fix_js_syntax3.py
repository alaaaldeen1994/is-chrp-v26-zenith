import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
script_path = os.path.join(base, 'js', 'script.js')

with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Fix line 6269 from '    },' to '    }\n};'
bad_snippet = """        } catch (e) {
            console.error(e);
            BiosimUI.notify('Manifest Error', 'Translation Engine Offline.', 'err');
        }
    },

window.runSafetyTest"""

fixed_snippet = """        } catch (e) {
            console.error(e);
            BiosimUI.notify('Manifest Error', 'Translation Engine Offline.', 'err');
        }
    }
};

window.runSafetyTest"""

if bad_snippet in content:
    content = content.replace(bad_snippet, fixed_snippet)
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Closed BiosimExpert object with }; before global window functions!")
else:
    print("Snippet not matched")

# Run Node syntax check
res = subprocess.run(['node', '-c', script_path], capture_output=True, text=True)
print("Node syntax check exit code:", res.returncode)
if res.returncode != 0:
    print("Stderr:", res.stderr)
else:
    print("🎉 SYNTAX 100% PERFECT! Node verified 0 syntax errors in js/script.js!")
