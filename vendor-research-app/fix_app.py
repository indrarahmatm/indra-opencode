with open("app.py", "r") as f:
    content = f.read()

old = """            for vr in research_data['results']:
                vendor_name = vr['vendor']
                with st.expander(f'M-^_M-^SM-^A {vendor_name}', expanded=True):
                    for search in vr['searches']:
                        query_text = search['query']
                        st.markdown(f'**Query:** {query_text}')
                        st.markdown(format_search_results(search['results']))
                        st.divider()"""

new = """            for vr in research_data['results']:
                vendor_name = vr['vendor']
                with st.expander(f'M-^_M-^SM-^A {vendor_name}', expanded=True):
                    for search in vr['searches']:
                        query_text = search['query']
                        translated_query = translate_text(query_text.replace('site:', ' situs:').replace('OR', ' atau '))
                        st.markdown(f'**Pencarian:** {translated_query}')
                        st.markdown(format_search_results(search['results']))
                        st.divider()"""

if old in content:
    content = content.replace(old, new)
    with open("app.py", "w") as f:
        f.write(content)
    print("Done")
else:
    print("Not found - checking for double quotes")
    old2 = """            for vr in research_data[\"results\"]:
                vendor_name = vr[\"vendor\"]
                with st.expander(f\"M-^_M-^SM-^A {vendor_name}\", expanded=True):
                    for search in vr[\"searches\"]:
                        query_text = search[\"query\"]
                        st.markdown(f\"**Query:** {query_text}\")
                        st.markdown(format_search_results(search[\"results\"]))
                        st.divider()"""
    if old2 in content:
        print("Found double quote version")
        new2 = """            for vr in research_data[\"results\"]:
                vendor_name = vr[\"vendor\"]
                with st.expander(f\"M-^_M-^SM-^A {vendor_name}\", expanded=True):
                    for search in vr[\"searches\"]:
                        query_text = search[\"query\"]
                        translated_query = translate_text(query_text.replace(\"site:\", \" situs:\").replace(\"OR\", \" atau \"))
                        st.markdown(f\"**Pencarian:** {translated_query}\")
                        st.markdown(format_search_results(search[\"results\"]))
                        st.divider()"""
        content = content.replace(old2, new2)
        with open("app.py", "w") as f:
            f.write(content)
        print("Fixed")
    else:
        print("Still not found")
