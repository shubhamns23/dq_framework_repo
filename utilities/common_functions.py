import hashlib
import json
import time

from pyspark.sql.functions import col

from common.constants import (COL_ENTITY_ID, COL_ENTITY_METADATA,
                              COL_ENTITY_NAME, COL_EP_ID, COL_ERROR_FILE_PATH,
                              COL_INPUT_FILE_PATH, COL_OUTPUT_FILE_PATH,
                              COL_RULE_ID, COL_RULE_NAME, PROP_FILE_FORMAT,
                              PROP_FORMAT_DETAILS, VAR_ENTITY_ID)
from common.custom_logger import get_logger


# Extracts the active execution plan from the provided DataFrame
# by filtering rows where
# is_active is "Y". Converts the filtered data into a list of tuples
# for further processing.
def get_active_execution_plans(execution_plan_with_rule_df):
    """
    try:
        logger = get_logger()
        plan_list = [
            tuple(row)
            for row in execution_plan_with_rule_df.filter(
                execution_plan_with_rule_df.is_active == "Y"
            ).collect()
        ]
        logger.info(
            "[DQ_GET_ACTIVE_PLANS] Active execution plans "
            "fetched successfully from execution plan table."
        )
        return plan_list
    except Exception as e:
        logger.error(
            f"[DQ_GET_ACTIVE_PLANS] Exception occured in "
            f"fetch_execution_plan():{e}"
        )
        return None
    """
    try:
        logger = get_logger()
        # Select only necessary columns and convert to list of tuples
        plan_list = (
            execution_plan_with_rule_df
            .filter(col("is_active") == "Y")
            .rdd.map(tuple)
            .collect()
        )
        logger.info(
            "[DQ_GET_ACTIVE_PLANS] Active execution plans "
            "fetched successfully from execution plan table."
        )
        return plan_list
    except Exception as e:
        logger.error(
            f"[DQ_GET_ACTIVE_PLANS] Exception occurred in "
            f"fetch_execution_plan(): {e}"
        )
        return None


# Merges the execution plan DataFrame with the rules DataFrame using
# 'rule_id' as the key.
# Drops duplicate or unnecessary columns and orders the result by 'ep_id'.
def join_execution_plan_with_rules(execution_plan_df, rules_df):
    try:
        logger = get_logger()
        execution_plan_with_rules_df = (
            execution_plan_df.join(
                rules_df.select(COL_RULE_ID, COL_RULE_NAME),
                execution_plan_df.rule_id == rules_df.rule_id,
                "inner"
            )
            .drop(execution_plan_df.last_update_date)
            .drop(rules_df.rule_id)
            .orderBy(COL_EP_ID)
        )
        logger.info(
            "[DQ_JOIN_PLANS_AND_RULES] Execution plans and rules joined "
            "successfully for data quality processing."
        )
        return execution_plan_with_rules_df
    except Exception as e:
        logger.error(
            f"[DQ_JOIN_PLANS_AND_RULES] Exception occured in "
            f"join_execution_plan_with_rules(): {e}"
        )


# fetch path from entity master table path
def fetch_entity_columns(entity_filtered_master_df, entity_id):
    """
    try:
        logger = get_logger()
        # Filter the dataframe for the specific entity_id and
        # select required columns
        result = (
            entity_filtered_master_df
            .filter(col(COL_ENTITY_ID) == entity_id)
            .select(
                COL_INPUT_FILE_PATH,
                COL_OUTPUT_FILE_PATH,
                COL_ERROR_FILE_PATH,
                COL_ENTITY_METADATA,
                COL_ENTITY_NAME
            )
            .first()
        )
        # Initialize paths as None
        (input_file_path, output_file_path, error_file_path,
            entity_metadata, entity_name) = (
            None, None, None, None, None
        )

        if result:
            if result[COL_INPUT_FILE_PATH]:
                input_file_path = result[COL_INPUT_FILE_PATH]
            else:
                logger.error(f"[FETCH_ENTITY_PATH] Input file path "
                             f"not found for entity_id: {entity_id}")

            if result[COL_OUTPUT_FILE_PATH]:
                output_file_path = result[COL_OUTPUT_FILE_PATH]
            else:
                logger.error(f"[FETCH_ENTITY_PATH] Output file path "
                             f"not found for entity_id: {entity_id}")

            if result[COL_ERROR_FILE_PATH]:
                error_file_path = result[COL_ERROR_FILE_PATH]
            else:
                logger.error(f"[FETCH_ENTITY_PATH] Error file path "
                             f"not found for entity_id: {entity_id}")

            if result[COL_ENTITY_METADATA]:
                entity_metadata = result[COL_ENTITY_METADATA]
            else:
                logger.error(f"[FETCH_ENTITY_PATH] entity_metadata column "
                             f"not found for entity_id: {entity_id}")

            if result[COL_ENTITY_NAME]:
                entity_name = result[COL_ENTITY_NAME]
            else:
                logger.error(f"[FETCH_ENTITY_PATH] entity_name column "
                             f"not found for entity_id: {entity_id}")

            logger.info(f"[FETCH_ENTITY_PATH] Required columns retrieved "
                        f"for entity_id: {entity_id}")
        else:
            logger.error(f"[FETCH_ENTITY_PATH] No records found "
                         f"for entity_id: {entity_id}")

        return [
            input_file_path,
            output_file_path,
            error_file_path,
            entity_metadata,
            entity_name
        ]

    except Exception as e:
        logger.error(f"[FETCH_ENTITY_PATH] Error fetching file paths "
                     f"for entity_id: {entity_id} - {e}")
        return None, None, None, None, None
    """
    try:
        logger = get_logger()

        # Fetch entity details efficiently (limit the scan to 1 row)
        result = (
            entity_filtered_master_df
            .filter(col(COL_ENTITY_ID) == entity_id)
            .select(
                COL_INPUT_FILE_PATH,
                COL_OUTPUT_FILE_PATH,
                COL_ERROR_FILE_PATH,
                COL_ENTITY_METADATA,
                COL_ENTITY_NAME
            )
            .limit(1)
            .collect()
        )

        if not result:
            logger.error(
                f"[FETCH_ENTITY_PATH] No records found "
                f"for entity_id: {entity_id}"
            )
            return None  # Return None if entity_id is not found

        # Convert Row to dictionary for easy access
        entity_data = result[0].asDict()

        # Log missing columns in a single message instead of multiple logs
        missing_columns = [
            key for key, value in entity_data.items() if value is None
        ]
        if missing_columns:
            logger.error(
                f"[FETCH_ENTITY_PATH] Missing columns for "
                f"entity_id {entity_id}: {missing_columns}"
            )

        logger.info(
            f"[FETCH_ENTITY_PATH] Successfully fetched columns "
            f"for entity_id: {entity_id}"
        )

        return entity_data

    except Exception as e:
        logger.error(
            f"[FETCH_ENTITY_PATH] Error fetching file paths "
            f"for entity_id: {entity_id} - {e}"
        )
        return None


def fetch_rules(execution_plan_filtered__df):
    try:
        logger = get_logger()
        # Fetch distinct rule_ids from the dataframe and collect as a list
        rule_list = (
            execution_plan_filtered__df.select(COL_RULE_ID)
            .distinct()
            .rdd.flatMap(lambda x: x)
            .collect()
        )

        if not rule_list:
            logger.error(
                f"[FETCH_RULES] Rules does not exists in execution_plan_df "
                f"for entity_id={VAR_ENTITY_ID}"
            )
            return []
        # Log success
        logger.info("[FETCH_RULES] Successfully fetched rule list.")
        return rule_list
    except Exception as e:
        # Log error if something goes wrong
        logger.error(f"Error fetching rule list: {e}")
        return []


def fetch_filtered_rules(rule_list, rule_master_df):
    try:
        logger = get_logger()
        # Filter the rule_master_df for the given list of rule_ids
        rule_master_filtered_df = rule_master_df.filter(
            rule_master_df[COL_RULE_ID].isin(rule_list)
        )
        # Log success
        logger.info(
            f"[FETCH_FILTERED_RULES] Successfully "
            f"filtered {len(rule_list)} rules."
        )
        return rule_master_filtered_df
    except Exception as e:
        # Log error if filtering fails
        logger.error(f"Error filtering rules: {e}")
        return None


def extract_format_details(entity_metadata_config):
    try:
        logger = get_logger()
        try:
            entity_metadata_config = json.loads(entity_metadata_config)
        except json.JSONDecodeError as e:
            logger.error(f"[EXTRACT FORMAT DETAILS] Invalid JSON format:{e}")
            return None, None

        file_format = entity_metadata_config.get(PROP_FILE_FORMAT)
        if not file_format:
            logger.error("[EXTRACT FORMAT DETAILS] Missing 'file_format' "
                         "in entity_metadata_config")
            return None, None

        format_details = entity_metadata_config.get(PROP_FORMAT_DETAILS, {})
        if not isinstance(format_details, dict):
            logger.error("[EXTRACT FORMAT DETAILS] Incorrect format details "
                         "provided in entity_metadata. Please provide "
                         "format details in dict({}) format.")
            return file_format, None

        format_options = format_details.get(file_format, {})

        if not format_options:
            logger.info("[EXTRACT FORMAT DETAILS] No format options "
                        "provided.")
            return file_format, None

        return file_format, format_options

    except Exception as e:
        logger.error(f"[EXTRACT FORMAT DETAILS] Exception occurred "
                     f"in extract_format_details(): {e}")
        return None, None


# Function to generate the unique er_id using timestamp and hash
def generate_erid(var_entity_id, var_plan_id):
    """
    Generate a unique var_er_id based on entity_id, plan_id,
    and current timestamp.
    :param var_entity_id: Entity ID
    :param var_plan_id: Plan ID
    :return: A 6-digit unique identifier
    """
    hash_value = hashlib.sha256(
        f"{var_entity_id}-{var_plan_id}-{int(time.time() * 1000)}".encode()
    ).hexdigest()
    return int(hash_value, 16) % 900000 + 100000
