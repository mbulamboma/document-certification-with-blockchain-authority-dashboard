import uuid
import os
import hashlib
from flask import session
from utils import qrcode as qr
from utils import ipfs as fs
from utils import eth 
from utils import prompt as ai 
import PyPDF2

def certify(request, uploadFilePath, openai, ipfsBaseUrl, contract, user_address):
    data_response = {} 
    if 'file_to_certify' in session: 
        uniqueId = str(uuid.uuid4())
        filepath = session['file_to_certify'] 
        
        # read the file content
        with open(filepath, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            file_content = ''
            for page_num in range(len(pdf_reader.pages)):
                # Get the text content of the current page
                page = pdf_reader.pages[page_num]
                file_content += page.extract_text() 
            f.close()
 
        rowhashText = ai.getDocumentInfos(file_content, openai)
        hashText = hashlib.sha256(rowhashText.encode('utf-8')).hexdigest()
        if eth.checkIfExist(hashText, contract, user_address):
            data_response["success"] = False
            data_response["message"] = "The document already exits"
            return data_response
        
        pathOfTheCertifiedDocument = os.path.join(uploadFilePath, uniqueId+"-certified.pdf")
        easyUrlToVerifyTheDocument = f"http://localhost:5000/verify/{hashText}"
        qr.gen_certified_document(hashText, filepath, pathOfTheCertifiedDocument, easyUrlToVerifyTheDocument, uploadFilePath)

        ipfsIDHash = fs.uploadFile(pathOfTheCertifiedDocument, ipfsBaseUrl)
        eth.saveRecordInBlockChain(ipfsIDHash, hashText,  contract, user_address)
        
        data_response["success"] = True
        data_response["message"] = "The document is successfully certified."
        data_response["ipfs-url"] = f"http://127.0.0.1:8080/ipfs/{ipfsIDHash}"
        print(f"HASSSHH------  {ipfsIDHash}")
        return data_response 
    else:
        data_response["success"] = False
        data_response["message"] = "The file was not uploaded..."
        return data_response

        