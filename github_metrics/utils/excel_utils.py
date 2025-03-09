def format_excel_sheet(worksheet, dataframe, workbook):
    """Apply enhanced formatting to Excel worksheets with conditional formatting."""
    try:
        # Define standard formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True
        })
        
        date_format = workbook.add_format({
            'num_format': 'yyyy-mm-dd',
            'align': 'center'
        })
        
        number_format = workbook.add_format({
            'num_format': '#,##0',
            'align': 'right'
        })
        
        decimal_format = workbook.add_format({
            'num_format': '#,##0.0',
            'align': 'right'
        })
        
        text_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top'
        })
        
        # Formats for PR health indicators
        health_format_good = workbook.add_format({
            'bg_color': '#E6F4EA',  # Light green
            'font_color': '#137333'  # Dark green
        })
        
        health_format_bad = workbook.add_format({
            'bg_color': '#FCE8E6',  # Light red
            'font_color': '#C5221F'  # Dark red
        })
        
        # Format for pending changes status
        pending_format = workbook.add_format({
            'bg_color': '#FFF0B3',  # Light yellow
            'font_color': '#994C00'  # Dark orange
        })
        
        # Format for resolved changes status
        resolved_format = workbook.add_format({
            'bg_color': '#E6F4EA',  # Light green
            'font_color': '#137333'  # Dark green
        })
        
        # Format columns based on content type
        for idx, col in enumerate(dataframe.columns):
            max_len = max(
                dataframe[col].astype(str).apply(len).max() if not dataframe.empty else 0,
                len(str(col))
            ) + 2
            
            if 'Date' in col:
                worksheet.set_column(idx, idx, max(12, max_len), date_format)
            elif col in ['Days Open', 'Avg Days to Merge', 'PR Days Open']:
                worksheet.set_column(idx, idx, max(8, max_len), decimal_format)
            elif any(word in col for word in ['Count', 'Added', 'Deleted', 'Number', 'Total', 'PRs', 'Lines', 'Requests', 'Changes']):
                worksheet.set_column(idx, idx, max(8, max_len), number_format)
            elif col in ['Title', 'Commit Message', 'Labels', 'Approver Comment', 'Changed Files', 'Approver Teams']:
                worksheet.set_column(idx, idx, min(50, max_len), text_format)
            elif col == 'PR Health':
                worksheet.set_column(idx, idx, max(15, max_len))
                # Add conditional formatting for health column
                worksheet.conditional_format(1, idx, len(dataframe) + 1, idx, {
                    'type': 'text',
                    'criteria': 'containing',
                    'value': '❌',
                    'format': health_format_bad
                })
                worksheet.conditional_format(1, idx, len(dataframe) + 1, idx, {
                    'type': 'text',
                    'criteria': 'containing',
                    'value': '✅',
                    'format': health_format_good
                })
            elif col == 'Changes Status':
                worksheet.set_column(idx, idx, max(20, max_len))
                # Add conditional formatting for change request status
                worksheet.conditional_format(1, idx, len(dataframe) + 1, idx, {
                    'type': 'text',
                    'criteria': 'containing',
                    'value': 'pending',
                    'format': pending_format
                })
                worksheet.conditional_format(1, idx, len(dataframe) + 1, idx, {
                    'type': 'text',
                    'criteria': 'containing',
                    'value': 'resolved',
                    'format': resolved_format
                })
            else:
                worksheet.set_column(idx, idx, min(30, max_len), text_format)
            
            worksheet.write(0, idx, col, header_format)
        
        # Add alternating row colors for readability
        for row in range(1, len(dataframe) + 1):
            if row % 2 == 0:
                bg_format = workbook.add_format({'bg_color': '#F8F8F8'})
                worksheet.set_row(row, None, bg_format)
        
        # Freeze header row and left columns
        worksheet.freeze_panes(1, 2)
        
    except Exception as e:
        raise Exception(f"Error formatting Excel sheet: {str(e)}")