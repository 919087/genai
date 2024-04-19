import logging
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import (
    PyPDFLoader,
    DirectoryLoader,
    UnstructuredWordDocumentLoader,
)
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import UnstructuredExcelLoader
 
# Initialize logger
logger = logging.getLogger(__name__)
 
# Function to process text documents
def process_text_documents(documents, cfg):
    logger.info("Processing text documents...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg.CHUNK_SIZE, chunk_overlap=cfg.CHUNK_OVERLAP
    )
    texts = text_splitter.split_documents(documents)
 
    embeddings = HuggingFaceEmbeddings(
        model_name=cfg.EMBEDDINGS, model_kwargs={"device": "cpu"}
    )
    vectorstore = FAISS.from_documents(texts, embeddings)
    vectorstore.save_local(cfg.DB_FAISS_PATH)
    logger.info("Text documents processing completed.")
 
# Function to run ingestion process
def run_ingest(filename, app_config):
    logger = logging.getLogger(__name__)
    logger.info(f"Starting ingestion process for file: {filename}")
    supported_document_types = set(app_config.DOCUMENT_TYPE)
    file_extension = filename.split(".")[-1].lower()
    if file_extension == "pdf" and "pdf" in supported_document_types:
        loader_cls = PyPDFLoader
    elif file_extension == "txt" and "txt" in supported_document_types:
        loader_cls = DirectoryLoader  # Use DirectoryLoader for text files
    elif file_extension == "docx" and "docx" in supported_document_types:
        loader_cls = UnstructuredWordDocumentLoader
    elif file_extension == "xlsx" and "xlsx" in supported_document_types:
        loader_cls = UnstructuredExcelLoader
    else:
        logger.warning(f"Unsupported document type for file {filename}.")
        return
 
    if file_extension == "txt" and "txt" in supported_document_types:
        file_path = os.path.join(app_config.UPLOAD_FOLDER)
        loader = loader_cls(file_path, glob=str(filename))
 
    file_path = os.path.join(app_config.UPLOAD_FOLDER, filename)
    loader = loader_cls(file_path)
    documents = loader.load()
 
    if file_extension == "txt":
        process_text_documents(documents, app_config)  # Process text documents separately
    else:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=app_config.CHUNK_SIZE, chunk_overlap=app_config.CHUNK_OVERLAP
        )
        texts = text_splitter.split_documents(documents)
        embeddings = HuggingFaceEmbeddings(
            model_name=app_config.EMBEDDINGS, model_kwargs={"device": "cpu"}
        )
        vectorstore = FAISS.from_documents(texts, embeddings)
        vectorstore.save_local(app_config.DB_FAISS_PATH)
    try:
        # Update metadata status to 'ingested'
        collection.update_one(
            {"document": filename}, {"$set": {"status": "ingested"}}
        )
        logger.info(f"Status updated to 'ingested' for file: {filename}")
    except Exception as e:
        logger.error(f"Error updating status for file {filename}: {e}")
    logger.info(f"Ingestion process completed for file: {filename}")
 
# Other text processing functions can be added here as needed