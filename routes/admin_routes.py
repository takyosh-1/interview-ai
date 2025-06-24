import uuid
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify

from config.settings import employee_data, running_servers
from models.data_manager import load_shared_feedback_data, load_shared_employee_data, save_shared_employee_data
from services.employee_server import start_employee_server
from services.ai_service import generate_summary_with_ai

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/")
def admin_home():
    return render_template("admin_home.html")

@admin_bp.route("/create-employee-url", methods=["POST"])
def create_employee_url():
    data = request.get_json()
    employee_name = data.get("name", "").strip()
    department = data.get("department", "").strip()
    
    logger.info(f"Creating employee URL for {employee_name} in {department} department")
    
    if not employee_name or not department:
        logger.warning(f"Invalid employee URL creation request: name='{employee_name}', department='{department}'")
        return jsonify({"success": False, "error": "従業員名と部署を入力してください"})
    
    employee_id = str(uuid.uuid4())
    base_port = 5001
    port = base_port
    
    while port in [server['port'] for server in running_servers.values()]:
        port += 1
    
    employee_data[employee_id] = {
        'name': employee_name,
        'department': department,
        'created_at': datetime.now().isoformat(),
        'port': port
    }
    
    save_shared_employee_data(employee_data)
    
    if start_employee_server(employee_id, port):
        employee_url = f"http://localhost:{port}"
        logger.info(f"Successfully created employee URL for {employee_name}: {employee_url}")
        return jsonify({
            "success": True, 
            "employee_url": employee_url,
            "port": port,
            "employee_id": employee_id
        })
    else:
        logger.error(f"Failed to start employee server for {employee_name} on port {port}")
        return jsonify({"success": False, "error": "従業員サーバーの起動に失敗しました"})

@admin_bp.route("/employees")
def list_employees():
    logger.info("Fetching employee list")
    current_employee_data = load_shared_employee_data()
    
    employees = []
    for emp_id, emp_data in current_employee_data.items():
        server_info = running_servers.get(emp_id, {})
        employees.append({
            'id': emp_id,
            'name': emp_data['name'],
            'department': emp_data['department'],
            'created_at': emp_data['created_at'],
            'port': emp_data.get('port'),
            'url': server_info.get('url'),
            'status': 'running' if emp_id in running_servers else 'stopped'
        })
    return jsonify(employees)

@admin_bp.route("/dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")

@admin_bp.route("/data")
def admin_data():
    department_filter = request.args.get('department', 'all')
    employee_filter = request.args.get('employee', 'all')
    logger.info(f"Fetching admin data with filters - department: {department_filter}, employee: {employee_filter}")
    
    current_feedback = load_shared_feedback_data()
    
    filtered_data = current_feedback
    if department_filter != 'all':
        filtered_data = [f for f in filtered_data if f['department'] == department_filter]
    if employee_filter != 'all':
        filtered_data = [f for f in filtered_data if f['employee_id'] == employee_filter]
    
    departments = list(set([f['department'] for f in current_feedback]))
    
    unique_employees = {}
    for f in current_feedback:
        emp_id = f['employee_id']
        if emp_id not in unique_employees:
            unique_employees[emp_id] = {'id': emp_id, 'name': f['employee_name']}
    employees = list(unique_employees.values())
    
    analytics = {
        'total_feedback': len(filtered_data),
        'departments': departments,
        'employees': employees,
        'recent_feedback': sorted(filtered_data, key=lambda x: x['timestamp'], reverse=True)[:10],
        'department_counts': {},
        'employee_counts': {}
    }
    
    for dept in departments:
        analytics['department_counts'][dept] = len([f for f in current_feedback if f['department'] == dept])
    
    for emp in employees:
        analytics['employee_counts'][emp['id']] = len([f for f in current_feedback if f['employee_id'] == emp['id']])
    
    return jsonify({
        'feedback': filtered_data,
        'analytics': analytics
    })

@admin_bp.route("/summary")
def admin_summary():
    logger.info("Generating admin summary")
    current_feedback = load_shared_feedback_data()
    summary = generate_summary_with_ai(current_feedback)
    logger.info("Admin summary generated successfully")
    return jsonify({"summary": summary})

@admin_bp.route("/feedback/<feedback_id>")
def admin_feedback_detail(feedback_id):
    logger.info(f"Fetching feedback detail for ID: {feedback_id}")
    current_feedback = load_shared_feedback_data()
    feedback = next((f for f in current_feedback if f['id'] == feedback_id), None)
    if not feedback:
        logger.warning(f"Feedback not found for ID: {feedback_id}")
        return jsonify({"error": "フィードバックが見つかりません"}), 404
    logger.info(f"Successfully retrieved feedback detail for ID: {feedback_id}")
    return jsonify(feedback)
