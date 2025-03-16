import re
import unicodedata
import string
from typing import List, Dict, Any, Optional, Callable
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords

# Download NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class Preprocessor:
    """Base class for text preprocessing operations."""
    
    def __init__(self):
        self.stopwords = set(stopwords.words('english'))
    
    def clean_text(self, text: str, remove_html: bool = True, remove_urls: bool = True, 
                  remove_special_chars: bool = True) -> str:
        """Clean text by removing HTML tags, URLs, and special characters."""
        if not isinstance(text, str):
            return ""
        
        # Remove HTML tags
        if remove_html:
            text = BeautifulSoup(text, "html.parser").get_text()
        
        # Remove URLs
        if remove_urls:
            text = re.sub(r'http\S+', '', text)
        
        # Remove special characters
        if remove_special_chars:
            text = re.sub(r'[^\w\s]', '', text)
        
        return text
    
    def normalize_text(self, text: str, lowercase: bool = True, remove_accents: bool = True,
                      remove_stopwords: bool = False) -> str:
        """Normalize text by converting to lowercase, removing accents, and stopwords."""
        if not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        if lowercase:
            text = text.lower()
        
        # Remove accents
        if remove_accents:
            text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
        
        # Remove stopwords
        if remove_stopwords:
            words = text.split()
            text = ' '.join([word for word in words if word.lower() not in self.stopwords])
        
        return text
    
    def tokenize_text(self, text: str, tokenize_type: str = "word", min_token_length: int = 2) -> List[str]:
        """Tokenize text into words or sentences."""
        if not isinstance(text, str):
            return []
        
        if tokenize_type == "word":
            tokens = word_tokenize(text)
            # Filter by length
            tokens = [token for token in tokens if len(token) >= min_token_length]
            return tokens
        elif tokenize_type == "sentence":
            return sent_tokenize(text)
        else:
            raise ValueError(f"Unsupported tokenization type: {tokenize_type}")
    
    def handle_missing_data(self, data: List[Dict[str, Any]], strategy: str = "remove", 
                           fill_value: Optional[str] = None) -> List[Dict[str, Any]]:
        """Handle missing data in the dataset."""
        if strategy == "remove":
            # Remove rows with missing values
            return [row for row in data if all(value is not None and value != "" for value in row.values())]
        elif strategy == "fill":
            # Fill missing values
            if fill_value is None:
                fill_value = ""
            
            result = []
            for row in data:
                new_row = {key: (value if value is not None and value != "" else fill_value) for key, value in row.items()}
                result.append(new_row)
            
            return result
        else:
            raise ValueError(f"Unsupported missing data strategy: {strategy}")
    
    def transform_data(self, data: List[Dict[str, Any]], method: str, columns: List[str]) -> List[Dict[str, Any]]:
        """Transform data using various methods."""
        if method == "clean_text":
            return self._apply_to_columns(data, columns, self.clean_text)
        elif method == "normalize_text":
            return self._apply_to_columns(data, columns, self.normalize_text)
        elif method == "tokenize_text":
            # For tokenization, we need to handle the list result
            result = []
            for row in data:
                new_row = row.copy()
                for column in columns:
                    if column in row:
                        new_row[f"{column}_tokens"] = self.tokenize_text(row[column])
                result.append(new_row)
            return result
        else:
            raise ValueError(f"Unsupported transformation method: {method}")
    
    def _apply_to_columns(self, data: List[Dict[str, Any]], columns: List[str], 
                         func: Callable[[str], str]) -> List[Dict[str, Any]]:
        """Apply a function to specified columns in the dataset."""
        result = []
        for row in data:
            new_row = row.copy()
            for column in columns:
                if column in row:
                    new_row[column] = func(row[column])
            result.append(new_row)
        return result 