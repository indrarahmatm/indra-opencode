from deep_translator import GoogleTranslator

t = GoogleTranslator(source="auto", target="id")
result = t.translate("Laptop specifications and features for business")
print(result)
