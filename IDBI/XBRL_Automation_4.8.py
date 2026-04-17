#################### ! Final Code for both taxanomy ############################################################
from pywinauto import Application
import time
from pywinauto.keyboard import send_keys
from pywinauto import Desktop
import os
import psutil
import pandas as pd

tool_path = r"D:\MCA\XBRLTool.exe"
tool_dir = os.path.dirname(tool_path)


def initiate_XBRL_tool(selected_taxanomy):
    ########################### Open XBRL tool ###################################################
    # app = Application(backend="uia").start(
    #     r"C:\Users\PC\Documents\MCA_XBRL_Valiation_Tool_V5.1@16-09-2025\XBRLTool.exe"
    # )
    app = Application(backend="uia").start(
    f'"{tool_path}"',
    work_dir=tool_dir   # ✅ CRITICAL FIX
    )

    
    dlg = Desktop(backend="uia").window(title_re=".*XBRL Validation Tool.*")

    # ---------------- Select Taxanomy IND-AS 2017---------------- #
    time.sleep(1)
    send_keys("%T")
    time.sleep(1)
    send_keys("%S")
    time.sleep(1)
    if selected_taxanomy == 2017:
        send_keys('{DOWN}')  
    time.sleep(1)
    send_keys('{ENTER}')

    # ---------------- WAIT FOR POPUP to appear after Taxanomy loaded properly ---------------- #
    # Access Message dialog
    msg_dlg = dlg.child_window(title="Message", control_type="Window")
    msg_dlg.wait("visible", timeout=600)
    time.sleep(1)
    msg_dlg.child_window(title="Close", control_type="Button").click_input()
    time.sleep(0.2)
    # time.sleep(130)
    # send_keys('{ENTER}')
    # time.sleep(0.5)
    return dlg

def close_XBRL(dlg):
    try:
        pid = dlg.process_id()
        print("Killing PID:", pid)
        psutil.Process(pid).terminate()
        time.sleep(1)
        # return False
    except Exception as e:
        print("Closing XBRL for incorrect schema or taxanomy exception :", e)
# dlg = initiate_XBRL_tool()
xml_dir = r"D:\\Kripal\\IDBI\\annual_filing_xml"      # folder containing PDFs

def process_xml(xml_file, selected_taxanomy):
    # if "Standalone" in xml_file and '2025' in xml_file:
    if '.xml' in xml_file:
        dlg = initiate_XBRL_tool(selected_taxanomy)
        year = xml_file.split("_")[-1].replace(".xml", "")
        cin = xml_file.split("_")[0]
        # if not xml_file.lower().endswith(".xml"):
        #     continue

        pdf_path = os.path.join(xml_dir, xml_file)
        print(pdf_path)

    # for i in range(5):
        # ---------------- Click on file > Open and enter input file name box ---------------- #
        send_keys("%F")
        time.sleep(1)
        send_keys("%O")
        time.sleep(2)
        # Ensure cursor is in File name box
        send_keys('%N')          # Alt+N → File name (standard)
        time.sleep(1)

        # ---------------- Enter xml path in input file name box then click open and wait for processing ---------------- #
        # send_keys(r'D:\Nexensus_Projects\IDBI\aoc4_xml\564679389_L15421UP1993PLC018642-FS-2024-2025_10.xml')
        send_keys(pdf_path)
        time.sleep(2)
        send_keys('{ENTER}')
        time.sleep(1)

        # Access Document loaded successfull dialog
        doc_loading_dlg = dlg.child_window(title="Document has been loaded successfully..", control_type="Window")
        incorrect_schema_dlg = dlg.child_window(title="INFORMATION MESSAGE", control_type="Window")
        incorrect_taxanomy_dlg = dlg.child_window(title="MCA 21 validation Tool", control_type="Window")
        restart_tool_dlg = dlg.child_window(title="MCA21 XBRL Validation Tool", control_type="Window")
        if incorrect_schema_dlg.exists(timeout=60) or incorrect_taxanomy_dlg.exists(timeout=60):
            if incorrect_schema_dlg.exists():
                print("Incorrect Schema")
                send_keys('{ENTER}')
                time.sleep(2)
                try:
                    close_XBRL(dlg)
                except:
                    pass
                return False
                # dlg = initiate_XBRL_tool()
                # time.sleep(3)
            elif incorrect_taxanomy_dlg.exists():
                print("Current Taxanomy not supported")
                send_keys('{ENTER}')
                time.sleep(3)
            try:
                close_XBRL(dlg)
            except:
                pass
            return False
            # continue
        # elif restart_tool_dlg.exists(timeout=250):
        #     # elif restart_tool_dlg.exists():
        #     print("Restart the tool")
        #     send_keys('{ENTER}')
        #     time.sleep(3)
        #     try:
        #         close_XBRL(dlg)
        #     except:
        #         pass
        #     return False


        doc_loading_dlg.wait("visible", timeout=600)
        time.sleep(0.5)
        print("doc_loading_dlg visible now clicking ok")
        send_keys('{ENTER}')
        # doc_loading_dlg.child_window(title="Close", control_type="Button").click_input()
        time.sleep(0.5)

        # ---------------- Click File > Export to pdf then insert pdf path in input box to store pdf with required name ---------------- #
        send_keys("%F")
        time.sleep(1)
        send_keys("%E")
        time.sleep(1)
        # cin = 'L15421UP1993PLC018642'
        # year = '2025'
        time.sleep(0.5)
        send_keys('%N')
        time.sleep(0.3)
        send_keys(
            r"D:\\Kripal\\IDBI\\annual_filing_pdfs\\{}_Annual_Filing_{}.pdf".format(cin, year)
        )
        time.sleep(1)
        send_keys('{ENTER}')

        # ---------------- Waiting for pdf to be saved and click popup appeared ---------------- #
        # time.sleep(1)
        # send_keys('{ENTER}')
        # time.sleep(15)
        pdf_export_success_dlg = dlg.child_window(title="Message", control_type="Window")
        if pdf_export_success_dlg.exists(timeout=160):
            send_keys('{ENTER}')
            time.sleep(15)
        print("pdf saved successfully")
        # ######################## Close the XBRL tool ##########################################
        pid = dlg.process_id()
        print("Killing PID:", pid)
        psutil.Process(pid).terminate()
        time.sleep(1)
        return True
    
converted_pdfs = os.listdir(r"D:\Kripal\IDBI\annual_filing_pdfs")
excel_path = r"D:\\Kripal\\IDBI\\input_data\\non_converted_xmls.xlsx"

# Load existing Excel or create empty list if file doesn't exist
if os.path.exists(excel_path):
    non_converted_xmls = pd.read_excel(excel_path)['xml_file'].tolist()
else:
    non_converted_xmls = []
for xml_file in os.listdir(xml_dir)[:]:
    print(xml_file)
    if "2025.xml" in xml_file:
        print(
            "2025 xml file"
        )
        continue
    
    if xml_file.replace(".xml", ".pdf") in converted_pdfs or xml_file in non_converted_xmls:
        print("xml already converted or non-convertable")
        continue
    else:
        result_2017_taxanomy = process_xml(xml_file, 2017)
        if result_2017_taxanomy == True:
            print("xml converted with taxanomy 2017")
            continue
        else:
            result_2016_taxanomy = process_xml(xml_file, 2016)
            if result_2016_taxanomy == True:
                print("xml converted with taxanomy 2016")
            else:
                if xml_file not in non_converted_xmls:
                    non_converted_xmls.append(xml_file)
                    non_converted_xmls_df = pd.DataFrame(non_converted_xmls, columns=["xml_file"])
                    non_converted_xmls_df.to_excel(excel_path, index=False)
            