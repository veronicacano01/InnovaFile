from app import create_app

from services.document_content_service import (
    index_all_documents
)


# ============================================================
# APLICACIÓN
# ============================================================

app = create_app()


# ============================================================
# EJECUTAR INDEXACIÓN
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "============================================"
    )
    print(
        "      INNOVAFILE - INDEXACIÓN DOCUMENTAL"
    )
    print(
        "============================================"
    )
    print()

    with app.app_context():

        result = index_all_documents(
            root_path=app.root_path,
            upload_folder=app.config[
                "UPLOAD_FOLDER"
            ]
        )

        print(
            f"Documentos encontrados: "
            f"{result['total']}"
        )

        print(
            f"Indexados correctamente: "
            f"{result['indexed']}"
        )

        print(
            f"Sin texto extraíble: "
            f"{result['empty']}"
        )

        print(
            f"No compatibles: "
            f"{result['unsupported']}"
        )

        print(
            f"Errores: "
            f"{result['errors']}"
        )

        print()
        print(
            "--------------------------------------------"
        )

        for detail in result[
            "details"
        ]:

            status = detail.get(
                "status",
                ""
            )

            title = detail.get(
                "title",
                "Sin título"
            )

            if status == "indexed":

                symbol = "[OK]"

            elif status == "empty":

                symbol = "[SIN TEXTO]"

            elif status == "unsupported":

                symbol = "[NO COMPATIBLE]"

            else:

                symbol = "[ERROR]"

            print(
                f"{symbol} {title}"
            )

            if detail.get(
                "error"
            ):

                print(
                    "       "
                    +
                    detail[
                        "error"
                    ]
                )

        print()
        print(
            "============================================"
        )
        print(
            "             PROCESO FINALIZADO"
        )
        print(
            "============================================"
        )
        print()