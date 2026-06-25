L1380: 
L1381:     global zenith_foundation_v1, zenith_foundation_486k, model_mode
L1382:     base_dir = os.path.abspath(os.path.dirname(__file__))
L1383: 
L1384:     if SCVI_AVAILABLE:
L1385:         # ================================================================
L1386:         # ZENITH v29.0 ENSEMBLE MODEL SYSTEM (2-Model Architecture)
L1387:         # 1. 1.94M-cell Global Generalist Model
L1388:         # 2. 486k-cell HCA Specialist Model
L1389:         # ================================================================
L1390: 
L1391:         model_dir_1_94m = os.path.join(base_dir, "models", "zenith_foundation_v1")
L1392:         model_pt_1_94m = os.path.join(model_dir_1_94m, "model.pt")
L1393: 
L1394:         model_dir_486k = os.path.join(base_dir, "models", "scvi_model_486k_real")
L1395:         model_pt_486k = os.path.join(model_dir_486k, "model.pt")
L1396: 
L1397:         import psutil
L1398:         total_ram_gb = psutil.virtual_memory().total / (1024**3)
L1399:         load_1_94m = True
L1400:         if total_ram_gb < 1.5:
L1401:             print(f"[SYSTEM] Low memory detected ({total_ram_gb:.1f}GB). Skipping 1.94M model to prevent OOM.")
L1402:             load_1_94m = False
L1403: 
L1404:         # --- HUGGING FACE DYNAMIC MODEL DOWNLOADER ---
L1405:         import httpx
L1406:         import time
L1407:         import json
L1408:         
L1409:         def download_hf_file(repo_id: str, file_path: str, local_path: str, retries=3):
L1410:             # If the file exists and is larger than 5KB, it's a real model. If < 5KB, it's a Git LFS pointer.
L1411:             if os.path.exists(local_path) and os.path.getsize(local_path) > 5120:
L1412:                 return
L1413:             
L1414:             url = f"https://huggingface.co/datasets/{repo_id}/resolve/main/{file_path}?download=true"
L1415:             os.makedirs(os.path.dirname(local_path), exist_ok=True)
L1416:             
L1417:             for attempt in range(retries):
L1418:                 print(f"[ZENITH DOWNLOADER] Fetching {file_path} from Hugging Face (Attempt {attempt+1}/{retries})...")
L1419:                 try:
L1420:                     with httpx.Client(timeout=600.0, follow_redirects=True) as client:
L1421:                         with client.stream("GET", url) as response:
L1422:                             response.raise_for_status()
L1423:                             with open(local_path, "wb") as f:
L1424:                                 for chunk in response.iter_bytes(chunk_size=8192):
L1425:                                     f.write(chunk)
L1426:                     print(f"[ZENITH DOWNLOADER] Successfully downloaded {file_path}")
L1427:                     return
L1428:                 except Exception as e:
L1429:                     print(f"[ZENITH DOWNLOADER] Error on attempt {attempt+1}: {e}")
L1430:                     if attempt < retries - 1:
L1431:                         time.sleep(2)
L1432:             print(f"[ZENITH DOWNLOADER] Failed to download {file_path} after {retries} attempts.")
L1433: 
L1434:         # Download necessary models
L1435:         hf_repo = "alaaaldeen1994/zenith-models"
L1436:         download_hf_file(hf_repo, "models/scvi_model_486k_real/model.pt", model_pt_486k)
L1437:         if load_1_94m:
L1438:             download_hf_file(hf_repo, "models/zenith_foundation_v1/model.pt", model_pt_1_94m)
L1439:             download_hf_file(hf_repo, "models/zenith_foundation_v1/var_schema.h5ad", os.path.join(model_dir_1_94m, "var_schema.h5ad"))
L1440:             download_hf_file(hf_repo, "models/zenith_foundation_v1/umap_latent.h5ad", os.path.join(model_dir_1_94m, "umap_latent.h5ad"))
L1441: 
L1442:         # --- HUGGING FACE PYTORCH HOTFIX ---
L1443:         # scvi-tools versions sometimes add a blank 'pyro_param_store' to the state_dict which crashes newer/older versions on load
L1444:         def patch_scvi_state_dict(model_pt_path):
L1445:             import torch
L1446:             if not os.path.exists(model_pt_path): return
L1447:             try:
L1448:                 sd = torch.load(model_pt_path, map_location='cpu')
L1449:                 patched = False
L1450:                 
L1451:                 # It might be at the top level
L1452:                 if 'pyro_param_store' in sd:
L1453:                     del sd['pyro_param_store']
L1454:                     patched = True
L1455:                 
L1456:                 # Or it might be inside the 'model_state_dict' (scvi-tools standard)
L1457:                 if 'model_state_dict' in sd and isinstance(sd['model_state_dict'], dict):
L1458:                     if 'pyro_param_store' in sd['model_state_dict']:
L1459:                         del sd['model_state_dict']['pyro_param_store']
L1460:                         patched = True
L1461:                 
L1462:                 if patched:
L1463:                     torch.save(sd, model_pt_path)
L1464:                     print(f"[ZENITH HOTFIX] Cleaned incompatible state_dict keys in {model_pt_path}")
L1465:             except Exception as e:
L1466:                 print(f"[ZENITH HOTFIX] Failed to patch {model_pt_path}: {e}")
L1467:                 
L1468:         patch_scvi_state_dict(model_pt_486k)
L1469:         patch_scvi_state_dict(model_pt_1_94m)
L1470: 
L1471:         # --- Load 1.94M Model ---
L1472:         if load_1_94m and os.path.exists(model_pt_1_94m):
L1473:             try:
L1474:                 print("[ZENITH ENSEMBLE] Loading 1.94M Global Generalist Model...")
L1475:                 import anndata as ad
L1476:                 import pandas as pd
L1477:                 schema_path = os.path.join(model_dir_1_94m, "var_schema.h5ad")
L1478:                 if os.path.exists(schema_path):
L1479:                     adata_schema = ad.read_h5ad(schema_path)
L1480:                     obs_df = pd.DataFrame(index=adata_schema.obs_names)
L1481:                     obs_df['dataset_id'] = pd.Categorical(['1c739a3e-c3f5-49d5-98e0-73975e751201'], 
L1482:                         categories=['1c739a3e-c3f5-49d5-98e0-73975e751201', '2adb1f8a-a6b1-4909-8ee8-484814e2d4bf', '2e9d2f32-4cfb-49b5-b990-cbf4c241214e', '364bd0c7-f7fd-48ed-99c1-ae26872b1042', '43245158-5ae1-4e71-a9a6-67eef49c26bc', '53d208b0-2cfd-4366-9866-c3c6114081bc', '65badd7a-9262-4fd1-9ce2-eb5dc0ca8039', '72955cdb-bd92-4135-aa52-21f33f9640db', 'd4e69e01-3ba2-4d6b-a15d-e7048f78f22e', 'd567b692-c374-4628-a508-8008f6778f22'])
L1483:                     obs_df['donor_id'] = pd.Categorical(['10_Chowdhury'], 
L1484:                         categories=['10_Chowdhury', '11_Chowdhury', '1221', '12_Chowdhury', '1600', '1666', '1681', '1702', '1708', '1723'])
L1485:                     obs_df['suspension_type'] = pd.Categorical(['cell'], 
L1486:                         categories=['cell', 'nucleus'])
L1487:                     obs_df['disease'] = pd.Categorical(['normal'], 
L1488:                         categories=['arrhythmogenic right ventricular cardiomyopathy', 'atherosclerosis', 'dilated cardiomyopathy', 'hypertrophic cardiomyopathy', 'myocardial infarction', 'myocarditis', 'non-compaction cardiomyopathy', 'normal'])
L1489:                     adata_schema.obs = obs_df
L1490:                     adata_schema.layers['counts'] = adata_schema.X.copy()
L1491:                     zenith_foundation_v1 = SCVI.load(model_dir_1_94m, adata=adata_schema)
L1492:                 else:
L1493:                     zenith_foundation_v1 = SCVI.load(model_dir_1_94m)
L1494:                 print("SUCCESS: 1.94M Model loaded.")
L1495:             except Exception as e:
L1496:                 print(f"WARNING: 1.94M model failed to load: {e}")
L1497:                 zenith_foundation_v1 = None
L1498: 
L1499:         # --- Load 486k Model ---
L1500:         if os.path.exists(model_pt_486k):
L1501:             try:
L1502:                 print("[ZENITH ENSEMBLE] Loading 486k HCA Specialist Model...")
L1503:                 import anndata as ad
L1504:                 index_path = os.path.join(model_dir_486k, "gene_index.json")
L1505:                 if os.path.exists(index_path):
L1506:                     with open(index_path, "r") as f:
L1507:                         genes = json.load(f).get("var_names", [])
L1508:                     blank_adata = ad.AnnData(X=np.zeros((1, len(genes)), dtype=np.float32))
L1509:                     blank_adata.var_names = genes
L1510:                     zenith_foundation_486k = SCVI.load(model_dir_486k, adata=blank_adata)
L1511:                 else:
L1512:                     zenith_foundation_486k = SCVI.load(model_dir_486k)
L1513:                 print("SUCCESS: 486k Model loaded.")
L1514:             except Exception as e:
L1515:                 print(f"WARNING: 486k model failed to load: {e}")
L1516:                 zenith_foundation_486k = None
L1517: 
L1518:         if zenith_foundation_v1 is not None or zenith_foundation_486k is not None:
L1519:             model_mode = "CLINICAL"
L1520: 
L1521:         # Priority 3: Mock fallback
L1522: 
L1523:         if zenith_foundation_v1 is None:
L1524: 
L1525:             print(f"Warning: No clinical model found.")
L1526: 
L1527:             print(f"  To activate: place model in models/scvi_model_194M/ or models/zenith_foundation_v1/")
L1528: 
L1529:             zenith_foundation_v1 = None
L1530: 
