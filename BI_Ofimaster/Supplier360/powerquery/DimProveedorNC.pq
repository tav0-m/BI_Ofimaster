let
    Source = Csv.Document(File.Contents(pRutaModelo & "DimProveedorNC.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true])
in
    Headers
