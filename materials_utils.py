import json
import requests
from datetime import datetime

DATA_FILE_PATH = "data/teacher_materials.json"


def get_materials():
    """
    Fetch teacher materials from GitHub JSON file.
    Returns a list of material dictionaries.
    """
    try:
        from github_utils import _get_github_config as get_config
        config = get_config()
        url = f"https://raw.githubusercontent.com/{config['repo']}/{config['branch']}/{DATA_FILE_PATH}"

        response = requests.get(url)
        if response.status_code == 404:
            # File doesn't exist yet, return empty list
            return []

        response.raise_for_status()
        materials = response.json()
        return materials if isinstance(materials, list) else []
    except Exception as e:
        # Return empty list instead of raising error for better resilience
        return []


def save_materials(materials):
    """
    Save teacher materials to GitHub JSON file.
    """
    try:
        from github_utils import upload_to_github

        # Convert materials to JSON
        json_bytes = json.dumps(materials, indent=2).encode('utf-8')

        # Upload to GitHub
        upload_to_github(
            file_bytes=json_bytes,
            file_path=DATA_FILE_PATH,
            commit_message="Update teacher materials"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to save materials: {e}")


def add_material(class_id, course_code, course_title, filename, storage_path, 
                 file_url, content_type, size, uploaded_by, section=None):
    """
    Add a new teacher material.
    
    Args:
        section: The section this material is for. If not provided, will be extracted from class_id.
    """
    materials = get_materials()

    # Generate a simple ID
    material_id = f"mat_{len(materials) + 1}_{int(datetime.utcnow().timestamp())}"
    
    # Extract section from class_id if not provided
    if not section:
        from role_utils import get_section_from_class_id
        section = get_section_from_class_id(class_id)

    new_material = {
        "id": material_id,
        "class_id": class_id,
        "section": section,
        "course_code": course_code,
        "course_title": course_title,
        "filename": filename,
        "storage_path": storage_path,
        "file_url": file_url,
        "content_type": content_type,
        "size": size,
        "uploaded_by": uploaded_by,
        "uploaded_at": datetime.utcnow().isoformat()
    }

    materials.append(new_material)
    save_materials(materials)
    return material_id


def delete_material(material_id):
    """
    Delete a material by ID.
    """
    materials = get_materials()
    
    # Find the material to get its storage path
    material = None
    for mat in materials:
        if mat.get("id") == material_id:
            material = mat
            break
    
    if not material:
        raise ValueError(f"Material with ID {material_id} not found")
    
    # Delete from GitHub storage if storage_path exists
    storage_path = material.get("storage_path")
    if storage_path:
        try:
            from github_utils import delete_from_github
            delete_from_github(storage_path)
        except Exception as e:
            # Continue even if file deletion fails
            pass
    
    # Remove from materials list
    materials = [m for m in materials if m.get("id") != material_id]
    save_materials(materials)
    return material


def get_materials_by_section(class_id, section=None):
    """
    Get all materials for a specific section.
    
    Args:
        class_id: The class ID (format: {program}-{branch}-Sem{semester}-{section})
        section: Optional section to filter by. If not provided, extracted from class_id.
    
    Returns:
        List of material dictionaries accessible by this section only.
    """
    if not section:
        from role_utils import get_section_from_class_id
        section = get_section_from_class_id(class_id)
    
    materials = get_materials()
    return [m for m in materials if m.get("class_id") == class_id and m.get("section") == section]


def get_materials_by_class(class_id):
    """
    Get all materials for a specific class.
    """
    materials = get_materials()
    return [m for m in materials if m.get("class_id") == class_id]
