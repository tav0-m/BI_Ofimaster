let
    Source = Csv.Document(File.Contents(pRutaModelo & "DimProducto.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumns(Headers, {
        {"ExisteMaestro", each if _ = "" then null else Number.FromText(_, "en-US"), type number}
    })
in
    Typed
