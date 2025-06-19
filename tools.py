###############################
##  TOOLS
from langchain.agents import Tool
from langchain.tools import BaseTool
from langchain.tools import StructuredTool
import streamlit as st
from datetime import date
from dotenv import load_dotenv
import json
import re
import os
from transaction_db import TransactionDb

load_dotenv()

def get_current_user(input : str):
    db = TransactionDb()
    user = db.get_user(1)
    db.close()
    return user

get_current_user_tool = Tool(
    name='GetCurrentUser',
    func= get_current_user,
    description="Returns the current user for querying transactions."
)

def get_transactions(userId : str):
    """Returns the transactions associated to the userId provided by running this query: SELECT * FROM Transactions WHERE userId = ?."""
    try:
        db = TransactionDb()
        transactions = db.get_user_transactions(userId)
        db.close()
        return transactions
        
    except Exception as e:
        return f"Error: {e}'"
            

get_recent_transactions_tool = Tool(
    name='GetUserTransactions',
    func= get_transactions,
    description="Returns the transactions associated to the userId provided by running this query: SELECT * FROM Transactions WHERE userId = provided_userId."
)


def export_transactions_to_file(user_id):

    try:
        if not os.path.exists("exports"):
            os.makedirs("exports")
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            return json.dumps({"error": "Invalid user ID format"})
        
        
        filename = f"transaction-{user_id_int}"
        file_path = os.path.join("exports", filename)
        
        # Ensure the file path is within the exports directory (prevent path traversal)
        exports_dir = os.path.abspath("exports")
        full_file_path = os.path.abspath(file_path)
        if not full_file_path.startswith(exports_dir):
            return "Error: Invalid file path."
            
        db = TransactionDb()
        transactions = db.get_user_transactions(user_id_int)
        db.close()
        
        # FIXED: Use secure file writing instead of os.system()
        try:
            with open(full_file_path, 'w', encoding='utf-8') as f:
                f.write(transactions)
        except Exception as write_error:
            return f"Error writing file: {str(write_error)}"
        
        # Return a link to the file
        return f"Transactions for user {user_id} exported successfully. Access file at: http://192.168.189.131:8502/{file_path}"
        
    except Exception as e:
        return f"Error exporting transactions: {str(e)}"

export_transactions_tool = Tool(
    name='ExportTransactionsToFile',
    func=export_transactions_to_file,
    description="Exports transactions for a specific user to a text file. Input format: user_id (e.g., '1')"
)
