#!/usr/bin/env python3
"""
Finova Transaction Categorizer

This script uses Agent 6 to categorize transactions in a CSV file.
It adds a 'category' column to the input CSV file.

Usage:
    python categorize_transactions.py input.csv [output.csv]

Args:
    input.csv: Path to the input CSV file containing transactions
    output.csv (optional): Path for the output categorized CSV file
                          If not provided, uses input filename with '_categorized' suffix

Example:
    python categorize_transactions.py bank_statement.csv
    python categorize_transactions.py bank_statement.csv categorized_results.csv
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from main import run_agent6_categorizer


async def categorize_csv_file(input_path: str, output_path: str = None) -> str:
    """
    Categorize transactions in a CSV file using Agent 6.
    
    Args:
        input_path (str): Path to input CSV file
        output_path (str, optional): Path for output file
    
    Returns:
        str: Path to the categorized output file
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if not output_path:
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}_categorized.csv"
    
    print(f"📁 Reading CSV file: {input_path}")
    
    # Read the input CSV file
    with open(input_path, 'r', encoding='utf-8') as file:
        csv_content = file.read()
    
    print(f"🤖 Processing with Agent 6 Transaction Categorizer...")
    
    # Use Agent 6 to categorize the transactions
    categorized_csv = await run_agent6_categorizer(csv_content)
    
    # Save the categorized result
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(categorized_csv)
    
    print(f"✅ Categorized CSV saved to: {output_path}")
    return output_path


def main():
    """Main function to handle command line arguments and execute categorization."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result_path = asyncio.run(categorize_csv_file(input_file, output_file))
        print(f"\n🎉 Categorization complete!")
        print(f"📊 Input:  {input_file}")
        print(f"📈 Output: {result_path}")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()