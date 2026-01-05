"""
PRINAD - Streaming Sender v2.0
Sends CPFs to the API for real-time dashboard demonstration.
Now uses the new /simple_classify endpoint that fetches data from the database.
"""

import requests
import json
import time
import random
import argparse
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DADOS_DIR = BASE_DIR / "dados"

# Load CPFs from database
def load_available_cpfs(limit: int = 10000) -> List[str]:
    """Load available CPFs from the client database."""
    clientes_path = DADOS_DIR / "base_clientes.csv"
    
    if clientes_path.exists():
        df = pd.read_csv(clientes_path, sep=';', encoding='latin-1', usecols=['CPF'], nrows=limit)
        cpfs = df['CPF'].astype(str).str.zfill(11).tolist()
        print(f"Loaded {len(cpfs)} CPFs from base_clientes.csv")
        return cpfs
    
    # Fallback to base_cadastro
    cadastro_path = DADOS_DIR / "base_cadastro.csv"
    if cadastro_path.exists():
        df = pd.read_csv(cadastro_path, sep=';', encoding='latin-1', usecols=['CPF'], nrows=limit)
        cpfs = df['CPF'].astype(str).str.zfill(11).tolist()
        print(f"Loaded {len(cpfs)} CPFs from base_cadastro.csv")
        return cpfs
    
    print("Warning: No client database found!")
    return []


def send_cpf_to_api(api_url: str, cpf: str, endpoint: str = "simple_classify") -> Dict[str, Any]:
    """
    Send CPF to the API for classification.
    
    Args:
        api_url: Base API URL
        cpf: Client CPF
        endpoint: API endpoint to use
        
    Returns:
        API response as dictionary
    """
    try:
        response = requests.post(
            f"{api_url}/{endpoint}",
            json={"cpf": cpf},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "cpf": cpf}


def run_streaming(
    api_url: str, 
    interval: float, 
    count: int = -1, 
    verbose: bool = True,
    use_explained: bool = False
):
    """
    Run continuous streaming of CPFs from database.
    
    Args:
        api_url: Base API URL
        interval: Seconds between requests
        count: Number of requests (-1 for infinite)
        verbose: Print results
        use_explained: Use /explained_classify instead of /simple_classify
    """
    
    # Load available CPFs
    available_cpfs = load_available_cpfs()
    
    if not available_cpfs:
        print("Error: No CPFs available to stream!")
        return
    
    endpoint = "explained_classify" if use_explained else "simple_classify"
    
    print(f"\n{'='*70}")
    print("PRINAD Streaming Sender v2.0 - BACEN 4966")
    print(f"{'='*70}")
    print(f"API URL: {api_url}")
    print(f"Endpoint: /{endpoint}")
    print(f"Interval: {interval}s")
    print(f"Count: {'Infinite' if count < 0 else count}")
    print(f"Available CPFs: {len(available_cpfs)}")
    print(f"{'='*70}")
    
    # Check API health first
    try:
        health = requests.get(f"{api_url}/health", timeout=5).json()
        print(f"API Status: {health.get('status')}")
        print(f"Model Loaded: {health.get('model_loaded')}")
        print(f"Database Loaded: {health.get('database_loaded')}")
        print(f"Total Clientes: {health.get('total_clientes')}\n")
    except Exception as e:
        print(f"⚠️ Could not reach API: {e}")
        print("Make sure the API is running: uvicorn prinad.src.api:app\n")
        return
    
    sent = 0
    successes = 0
    errors = 0
    
    rating_counts = {}
    stage_counts = {1: 0, 2: 0, 3: 0}
    prinad_sum = 0.0
    
    try:
        while count < 0 or sent < count:
            # Select random CPF from available list
            cpf = random.choice(available_cpfs)
            
            # Send to API
            result = send_cpf_to_api(api_url, cpf, endpoint)
            sent += 1
            
            if 'error' in result:
                errors += 1
                if verbose:
                    print(f"[{sent}] ❌ CPF: ***{cpf[-4:]} | Error: {result['error']}")
            else:
                successes += 1
                rating = result.get('rating', 'Unknown')
                prinad = result.get('prinad', 0)
                stage = result.get('stage', 1)
                pd_12m = result.get('pd_12m', 0)
                
                rating_counts[rating] = rating_counts.get(rating, 0) + 1
                stage_counts[stage] = stage_counts.get(stage, 0) + 1
                prinad_sum += prinad
                
                if verbose:
                    # Color based on rating
                    if rating.startswith('A'):
                        color = '🟢'
                    elif rating.startswith('B'):
                        color = '🟡'
                    elif rating in ['C1', 'C2']:
                        color = '🟠'
                    else:
                        color = '🔴'
                    
                    print(f"[{sent}] {color} CPF: ***{cpf[-4:]} | "
                          f"PRINAD: {prinad:5.1f}% | Rating: {rating} | "
                          f"PD_12m: {pd_12m*100:.2f}% | Stage: {stage}")
            
            # Wait before next request
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n⛔ Streaming stopped by user")
    
    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY - BACEN 4966 Classification")
    print(f"{'='*70}")
    print(f"Total Sent: {sent}")
    print(f"Successes: {successes}")
    print(f"Errors: {errors}")
    
    if successes > 0:
        print(f"PRINAD Médio: {prinad_sum / successes:.2f}%")
    
    print(f"\n📊 Distribuição por Rating:")
    for rating in ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'D', 'DEFAULT']:
        cnt = rating_counts.get(rating, 0)
        if cnt > 0:
            pct = (cnt / successes * 100) if successes > 0 else 0
            bar = '█' * int(pct / 5)
            print(f"  {rating:8s}: {cnt:4d} ({pct:5.1f}%) {bar}")
    
    print(f"\n📈 Distribuição por Stage IFRS 9:")
    for stage in [1, 2, 3]:
        cnt = stage_counts.get(stage, 0)
        pct = (cnt / successes * 100) if successes > 0 else 0
        desc = {1: "Normal", 2: "Increased Risk", 3: "Default"}[stage]
        print(f"  Stage {stage} ({desc}): {cnt:4d} ({pct:5.1f}%)")
    
    print(f"{'='*70}")


def send_batch(api_url: str, cpfs: List[str], output_format: str = "json"):
    """
    Send batch of CPFs for classification.
    
    Args:
        api_url: Base API URL
        cpfs: List of CPFs
        output_format: 'json' or 'csv'
    """
    print(f"\n{'='*70}")
    print("PRINAD Batch Classification")
    print(f"{'='*70}")
    print(f"Sending {len(cpfs)} CPFs...")
    
    try:
        response = requests.post(
            f"{api_url}/multiple_classify",
            json={"cpfs": cpfs, "output_format": output_format},
            timeout=60
        )
        
        if response.status_code == 200:
            if output_format == "csv":
                # Save CSV response
                output_file = Path("classificacoes.csv")
                with open(output_file, 'w') as f:
                    f.write(response.text)
                print(f"✅ CSV saved to {output_file}")
            else:
                # Print JSON response
                result = response.json()
                print(f"✅ Success: {result.get('sucesso', 0)}")
                print(f"❌ Errors: {result.get('erro', 0)}")
                
                # Print first 5 results
                print("\nPrimeiros resultados:")
                for r in result.get('resultados', [])[:5]:
                    print(f"  CPF: ***{r.get('cpf', '')[-4:]} | "
                          f"PRINAD: {r.get('prinad', 0):.1f}% | "
                          f"Rating: {r.get('rating', '')} | "
                          f"Stage: {r.get('stage', 1)}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"{'='*70}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Send CPFs to PRINAD API for classification (BACEN 4966)'
    )
    parser.add_argument(
        '--api-url', '-u',
        default='http://localhost:8000',
        help='API base URL (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--interval', '-i',
        type=float,
        default=2.0,
        help='Seconds between requests (default: 2.0)'
    )
    parser.add_argument(
        '--count', '-c',
        type=int,
        default=-1,
        help='Number of requests to send (-1 for infinite)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress per-request output'
    )
    parser.add_argument(
        '--explained', '-e',
        action='store_true',
        help='Use /explained_classify endpoint (includes SHAP)'
    )
    parser.add_argument(
        '--batch', '-b',
        type=int,
        default=0,
        help='Send N random CPFs as batch instead of streaming'
    )
    parser.add_argument(
        '--batch-csv',
        action='store_true',
        help='Output batch as CSV instead of JSON'
    )
    
    args = parser.parse_args()
    
    if args.batch > 0:
        # Batch mode
        available_cpfs = load_available_cpfs(args.batch * 2)
        if available_cpfs:
            batch_cpfs = random.sample(available_cpfs, min(args.batch, len(available_cpfs)))
            send_batch(
                api_url=args.api_url,
                cpfs=batch_cpfs,
                output_format="csv" if args.batch_csv else "json"
            )
    else:
        # Streaming mode
        run_streaming(
            api_url=args.api_url,
            interval=args.interval,
            count=args.count,
            verbose=not args.quiet,
            use_explained=args.explained
        )


if __name__ == "__main__":
    main()
