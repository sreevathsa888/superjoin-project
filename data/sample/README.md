# Sample datasets

The supplied `starter-datasets.zip` has been unpacked below this folder for the demo. To refresh it from the original archive, run:

```powershell
Expand-Archive -LiteralPath C:\Users\ranga\Downloads\starter-datasets.zip -DestinationPath data\sample -Force
```

The application never reads this folder automatically. Upload any PDFs through the UI so the same pipeline is used for starter and unseen documents.

The repository intentionally contains no document-specific extraction logic or pre-populated fact records.
