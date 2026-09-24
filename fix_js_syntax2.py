import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
script_path = os.path.join(base, 'js', 'script.js')

with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Fix line 6269 }; to }
bad_snippet = """        } catch (e) {
            console.error(e);
            BiosimUI.notify('Manifest Error', 'Translation Engine Offline.', 'err');
    }
};"""

fixed_snippet = """        } catch (e) {
            console.error(e);
            BiosimUI.notify('Manifest Error', 'Translation Engine Offline.', 'err');
        }
    },"""

if bad_snippet in content:
    content = content.replace(bad_snippet, fixed_snippet)
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fixed line 6269 extra semicolon in js/script.js!")
else:
    print("Snippet 6269 not found, searching with regex...")

# Run Node syntax check
res = subprocess.run(['node', '-c', script_path], capture_output=True, text=True)
print("Node syntax check exit code:", res.returncode)
if res.returncode != 0:
    print("Stderr:", res.stderr)
else:
    print("🎉 SYNTAX PERFECT! 0 errors in js/script.js!")
