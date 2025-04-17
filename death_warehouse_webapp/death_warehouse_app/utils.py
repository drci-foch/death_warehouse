import logging

from django.db import DatabaseError, connections

logger = logging.getLogger(__name__)


def fetch_merged_data(page=1, page_size=25):
    offset = (page - 1) * page_size
    try:
        with connections["my_oracle"].cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    p.PATIENT_NUM,
                    p.LASTNAME,
                    p.FIRSTNAME,
                    p.BIRTH_DATE,
                    p.SEX,
                    p.EMAIL,
                    p.MAIDEN_NAME,
                    p.DEATH_DATE,
                    p.BIRTH_COUNTRY,
                    i.HOSPITAL_PATIENT_ID
                FROM DWH.DWH_PATIENT p
                JOIN DWH.DWH_PATIENT_IPPHIST i ON p.PATIENT_NUM = i.PATIENT_NUM
                OFFSET :offset ROWS FETCH NEXT :page_size ROWS ONLY""",
                {"offset": offset, "page_size": page_size},
            )
            result = cursor.fetchall()
            if not result:
                logger.warning("Query returned no results.")
                return None
            return result
    except DatabaseError as e:
        logger.error(f"Database error occurred: {e}")
        return None
