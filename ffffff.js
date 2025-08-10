<script>
  $(document).ready(function () {
    const $form = $("#target-group-form");
    const $recipientsTableBody = $("#recipients-table tbody");
    const $selectAll = $("#select-all-recipients");
    const $communicationForm = $("#communication-form");
    const userRole = $communicationForm.data("user-role");

    const fields = {
      branch: $("#id_branch"),
      role: $("#id_role"),
      staffType: $("#id_staff_type"),
      teaching: $("#id_teaching_positions"),
      nonTeaching: $("#id_non_teaching_positions"),
      studentClass: $("#id_student_class"),
      classArm: $("#id_class_arm"),
    };

    let selectedRecipients = new Set();

    // ===== Utility Functions =====

    function areFiltersEmpty() {
      // Check if all filters are empty or unchecked
      for (const key in fields) {
        const field = fields[key];

        // Skip logic for fields not relevant to userRole
        if ((userRole === "student" || userRole === "parent") && key !== "role") continue;
        if ((userRole !== "student" && userRole !== "parent") && key === "role") continue;

        if (field.is(":checkbox")) {
          if (field.prop("checked")) return false;
        } else {
          const val = field.val();
          if (val && val.toString().trim() !== "" && val !== "------------") return false;
        }
      }
      return true;
    }


    function saveFilters() {
      const filters = {};
      $form.find("select, input[type=checkbox]").each(function () {
        const $el = $(this);
        filters[$el.attr("id")] = $el.is(":checkbox") ? $el.prop("checked") : $el.val();
      });
      localStorage.setItem("targetGroupFilters", JSON.stringify(filters));
    }

    function clearFiltersStorage() {
      localStorage.removeItem("targetGroupFilters");
    }

    function clearSelectedRecipients() {
      selectedRecipients.clear();
      localStorage.removeItem("selectedRecipients");
    }

    function loadFilters() {
      const saved = localStorage.getItem("targetGroupFilters");
      if (!saved) return;
      const filters = JSON.parse(saved);
      for (const id in filters) {
        const $el = $("#" + id);
        if ($el.length) {
          if ($el.is(":checkbox")) {
            $el.prop("checked", filters[id]);
          } else {
            $el.val(filters[id]);
          }
        }
      }
    }

    function resetFields(keys) {
      keys.forEach((key) => {
        const field = fields[key];
        if (field.is("select")) {
          field.val("");
        } else {
          field.find("input[type=checkbox]").prop("checked", false);
        }
      });
    }

    function updateBranchVisibility() {
      if (fields.branch.val()) {
        $("#role-field").show();
      } else {
        $("#role-field, #staff-type-field, #teaching-positions-field, #non-teaching-positions-field, #student-class-field, #class-arm-field").hide();
        resetFields(["role", "staffType", "teaching", "nonTeaching", "studentClass", "classArm"]);
      }
    }

    function updateRoleVisibility() {
      const role = fields.role.val();
      if (role === "staff") {
        $("#staff-type-field").show();
        $("#student-class-field, #class-arm-field").hide();
        resetFields(["studentClass", "classArm"]);
        updateStaffTypeVisibility();
      } else if (role === "student") {
        $("#staff-type-field, #teaching-positions-field, #non-teaching-positions-field").hide();
        resetFields(["staffType", "teaching", "nonTeaching"]);
        $("#student-class-field").show();
        updateStudentClassVisibility();
      } else {
        $("#staff-type-field, #teaching-positions-field, #non-teaching-positions-field, #student-class-field, #class-arm-field").hide();
        resetFields(["staffType", "teaching", "nonTeaching", "studentClass", "classArm"]);
      }
    }

    function updateStaffTypeVisibility() {
      const type = fields.staffType.val();
      const $teaching = $("#teaching-positions-field");
      const $nonTeaching = $("#non-teaching-positions-field");

      if (type === "teaching") {
        $teaching.show();
        $nonTeaching.hide().find("input[type=checkbox]").prop("checked", false);
      } else if (type === "non_teaching") {
        $nonTeaching.show();
        $teaching.hide().find("input[type=checkbox]").prop("checked", false);
      } else if (type === "both") {
        $teaching.show();
        $nonTeaching.show();
      } else {
        $teaching.hide().find("input[type=checkbox]").prop("checked", false);
        $nonTeaching.hide().find("input[type=checkbox]").prop("checked", false);
      }
    }

    function updateStudentClassVisibility() {
      const show = !!fields.studentClass.val();
      $("#class-arm-field").toggle(show);
      if (!show) fields.classArm.val("");
    }

    function saveSelectedRecipients() {
      localStorage.setItem("selectedRecipients", JSON.stringify([...selectedRecipients]));
    }

    function loadSelectedRecipients() {
      selectedRecipients = new Set(JSON.parse(localStorage.getItem("selectedRecipients") || "[]"));
    }

    function updateRecipientTableCheckboxStates() {
      $(".recipient-checkbox").each(function () {
        const id = $(this).val();
        $(this).prop("checked", selectedRecipients.has(id));
      });
      $selectAll.prop(
        "checked",
        $(".recipient-checkbox:checked").length === $(".recipient-checkbox").length
      );
    }

    function loadRecipients() {
      // If no filters are applied, always show no users found message
      if (areFiltersEmpty()) {
        recipientsTable.clear().draw();
        $selectAll.prop("checked", false);
        $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">No users found.</td></tr>');
        return;
      }

      // Extra safeguard for student role — avoid sending request if student_class or class_arm is empty
      if (fields.role.val() === "student") {
        const studentClass = fields.studentClass.val();
        const classArm = fields.classArm.val();

        if (!studentClass || !classArm) {
          recipientsTable.clear().draw();
          $selectAll.prop("checked", false);
          $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">Please select class and arm to view students.</td></tr>');
          return;
        }
      }

      const queryData = $form.serializeArray().filter(item => {
      const val = item.value && item.value.trim();
      if (!val) return false;

      const role = fields.role.val();
      const staffType = fields.staffType.val();

      // Skip irrelevant fields
      if (role !== "student" && (item.name === "student_class" || item.name === "class_arm")) return false;
      if (role !== "staff" && item.name === "staff_type") return false;

      // Require at least one teaching/non-teaching checkbox for staff_type 'both'
      if (role === "staff") {
        const hasTeaching = fields.teaching.find("input:checked").length > 0;
        const hasNonTeaching = fields.nonTeaching.find("input:checked").length > 0;

        if (staffType === "both" && !hasTeaching && !hasNonTeaching) {
          recipientsTable.clear().draw();
          $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">Please select at least one Teaching or Non-Teaching position.</td></tr>');
          return false;
        }

        if (staffType === "non_teaching" && !hasNonTeaching) {
          recipientsTable.clear().draw();
          $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">Please select at least one Non-Teaching position.</td></tr>');
          return false;
        }

        if (staffType === "teaching" && !hasTeaching) {
          recipientsTable.clear().draw();
          $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">Please select at least one Teaching position.</td></tr>');
          return false;
        }
      }

      return true;
      });

      if (queryData.length === 0) {
        recipientsTable.clear().draw();
        $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">Please apply valid filters to see results.</td></tr>');
        return;
      }

      // Only make request when queryData is not empty
      $.get("{% url 'get_filtered_users' %}", $.param(queryData), function (response) {
          recipientsTable.clear();
          if (response.length === 0) {
            recipientsTable.draw();
            $selectAll.prop("checked", false);
            $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">No users found.</td></tr>');
            return;
          }

          response.forEach((user, index) => {
            const profilePic = (user.profile_picture && user.profile_picture.url) || "/static/assets/img/profile-pic.png";
            const isChecked = selectedRecipients.has(user.id.toString());

            recipientsTable.row.add([
              `<input type="checkbox" class="recipient-checkbox" value="${user.id}" ${isChecked ? "checked" : ""}>`,
              index + 1,
              `<img src="${profilePic}" alt="Profile Picture" width="30" height="30" style="border-radius: 50%; object-fit: cover;">`,
              user.branch__name,
              `${user.first_name} ${user.last_name}`,
              user.email,
            ]);
          });

          recipientsTable.draw();
          updateRecipientTableCheckboxStates();
        });
      }


    
    
    function handleDependencyChange() {
      clearSelectedRecipients();
      $selectAll.prop("checked", false);
      saveFilters();
      loadRecipients();
    }

    // ===== Event Bindings =====

    fields.branch.on("change", () => {
      updateBranchVisibility();
      updateRoleVisibility();
      handleDependencyChange();
    });

    fields.role.on("change", () => {
      updateRoleVisibility();
      handleDependencyChange();
    });

    fields.staffType.on("change", () => {
      updateStaffTypeVisibility();
      handleDependencyChange();
    });

    fields.studentClass.on("change", () => {
      updateStudentClassVisibility();
      handleDependencyChange();
    });

    $form.find("select, input[type=checkbox]").not("#select-all-recipients").on("change", handleDependencyChange);

    $recipientsTableBody.on("change", ".recipient-checkbox", function () {
      const id = $(this).val();
      if ($(this).is(":checked")) {
        selectedRecipients.add(id);
      } else {
        selectedRecipients.delete(id);
      }
      saveSelectedRecipients();
      updateRecipientTableCheckboxStates();
    });

    $selectAll.on("change", function () {
      const checked = this.checked;
      $(".recipient-checkbox").each(function () {
        $(this).prop("checked", checked);
        const id = $(this).val();
        if (checked) {
          selectedRecipients.add(id);
        } else {
          selectedRecipients.delete(id);
        }
      });
      saveSelectedRecipients();
    });

    $communicationForm.on("submit", function (e) {
      if (["staff", "branch_admin", "superadmin"].includes(userRole) && !fields.branch.val()) {
        alert("Please select a Branch before submitting the form.");
        e.preventDefault();
        return false;
      }

      if (["student", "parent"].includes(userRole) && !fields.role.val()) {
        alert("Please select a Role before submitting the form.");
        e.preventDefault();
        return false;
      }

      clearFiltersStorage();
      clearSelectedRecipients();

      $communicationForm.find('input[name="selected_recipients"]').remove();

      [...selectedRecipients].forEach(function (id) {
        $("<input>", {
          type: "hidden",
          name: "selected_recipients",
          value: id,
        }).appendTo($communicationForm);
      });
    });

    // ===== Attachments =====

    const maxAttachments = 10;
    let totalForms = parseInt($("#id_attachments-TOTAL_FORMS").val());

    $("#add-attachment").on("click", function () {
      if (totalForms >= maxAttachments) return alert("Maximum attachments reached.");

      const $newForm = $(".attachment-form:first").clone();
      $newForm.find("input, select, textarea").each(function () {
        const name = $(this).attr("name").replace("-0-", `-${totalForms}-`);
        const id = "id_" + name;
        $(this).attr({ name, id }).val("");
        if ($(this).is(":checkbox, :radio")) $(this).prop("checked", false);
      });

      $newForm.find(".remove-attachment").remove();
      $newForm.append('<button type="button" class="btn btn-danger remove-attachment" style="position: absolute; top: 10px; right: 10px;">Remove</button>');
      $("#attachments-container").append($newForm);

      totalForms++;
      $("#id_attachments-TOTAL_FORMS").val(totalForms);
    });

    $("#attachments-container").on("click", ".remove-attachment", function () {
      $(this).closest(".attachment-form").remove();
      totalForms--;
      $("#id_attachments-TOTAL_FORMS").val(totalForms);
    });


    // ===== Initial Load =====

    loadFilters();
    loadSelectedRecipients();
    updateBranchVisibility();
    updateRoleVisibility();
    updateStaffTypeVisibility();
    updateStudentClassVisibility();
    loadRecipients();
  });
</script> 



/////////////////////////////////////////////////////////////////////////////////////</input>



{% extends "base.html" %} {% load static %} {% block content %}
<h2 style="margin-bottom: 1rem">Create Communication</h2>

<style>
  #form-fields-container {
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 1rem;
    display: flex;
    flex-wrap: wrap; /* allow wrapping */
    gap: 1rem; /* spacing between fields */
    justify-content: flex-start; /* align fields left */
    align-items: flex-start; /* align items at top */
    /* Remove scroll and nowrap */
    overflow-x: visible;
    white-space: normal;
    /* New background color */
    background-color: #f9f9fb; /* very light gray-blue */

    /* Optional subtle shadow for nice depth */
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
  }

  #form-fields-container legend {
    font-weight: 600;
    font-size: 1.1rem;
    padding: 0 0.5rem;
    flex-basis: 100%; /* make legend take full width on its own line */
    margin-bottom: 1rem; /* space below legend */
  }

  .form-group {
    display: flex;
    flex-direction: column; /* label on top of input */
    min-width: 180px; /* minimum width for each group */
    flex-grow: 1;
    margin-top: -2rem;
    /* fields can grow to fill space */
  }

  .form-label {
    margin-bottom: 0.3rem;
    font-weight: 500;
  }
</style>


<form id="target-group-form" method="get" style="margin-bottom: 1rem">
  <fieldset id="form-fields-container">
    <legend>Select Target Group</legend>

    {% if user_role != "student" and user_role != "parent" %}
    <div id="branch-field" class="form-group">
      <label for="id_branch" class="form-label">Branch:</label>
      {{ target_group_form.branch }} {% if target_group_form.branch.errors %}
      <div class="text-danger" style="color: red; margin-top: 0.25rem">
        {{ target_group_form.branch.errors }}
      </div>
      {% endif %}
    </div>
    {% else %}
    <input
      type="hidden"
      id="id_branch"
      name="branch"
      value="{{ user_branch_id }}"
    />
    {% endif %}

    <div
      id="role-field"
      class="form-group"
      style="{% if target_group_form.role.errors %}display: block{% else %}display: none{% endif %}"
    >
      <label for="id_role" class="form-label">Role:</label>
      {{ target_group_form.role }} {% if target_group_form.role.errors %}
      <div class="text-danger" style="color: red; margin-top: 0.25rem">
        {{ target_group_form.role.errors }}
      </div>
      {% endif %}
    </div>

    <div id="staff-type-field" class="form-group" style="display: none">
      <label for="id_staff_type" class="form-label">Staff Type:</label>
      {{ target_group_form.staff_type }} 
      {% if target_group_form.staff_type.errors %}
      <div class="text-danger" style="color: red; margin-top: 0.25rem">
        {{ target_group_form.staff_type.errors }}
      </div>
      {% endif %}
    </div>

    <div id="teaching-positions-field" class="form-group" style="display: none">
      <label for="id_teaching_positions" class="form-label"
        >Teaching Positions:</label
      >
      {{ target_group_form.teaching_positions }} 
      {% if target_group_form.teaching_positions.errors %}
      <div class="text-danger" style="color: red; margin-top: 0.25rem">
        {{ target_group_form.teaching_positions.errors }}
      </div>
      {% endif %}
    </div>

    <div
      id="non-teaching-positions-field"
      class="form-group"
      style="display: none"
    >
      <label for="id_non_teaching_positions" class="form-label"
        >Non-Teaching Positions:</label
      >
      {{ target_group_form.non_teaching_positions }} 
      {% if target_group_form.non_teaching_positions.errors %}
      <div class="text-danger" style="color: red; margin-top: 0.25rem">
        {{ target_group_form.non_teaching_positions.errors }}
      </div>
      {% endif %}
    </div>

    <div id="student-class-field" class="form-group" style="display: none">
      <label for="id_student_class" class="form-label">Student Class:</label>
      {{ target_group_form.student_class }} 
      {% if target_group_form.student_class.errors %}
      <div class="text-danger" style="color: red; margin-top: 0.25rem">
        {{ target_group_form.student_class.errors }}
      </div>
      {% endif %}
    </div>

    <div id="class-arm-field" class="form-group" style="display: none">
      <label for="id_class_arm" class="form-label">Class Arm:</label>
      {{ target_group_form.class_arm }} 
      {% if target_group_form.class_arm.errors %}
      <div class="text-danger" style="color: red; margin-top: 0.25rem">
        {{ target_group_form.class_arm.errors }}
      </div>
      {% endif %}
    </div>
  </fieldset>
</form>


{% if communication_form.non_field_errors %}
  <div style="color: red; background-color: white; border: 1px solid red; padding: 0.75rem; margin-bottom: 1rem;">
    {% for error in communication_form.non_field_errors %}
      <div>{{ error }}</div>
    {% endfor %}
  </div>
{% endif %}




<h3 style="margin-bottom: 1rem">Filtered Recipients</h3>
<table
  id="recipients-table"
  class="table table-striped"
  style="width: 100%; border-collapse: collapse; margin-bottom: 2rem"
>
  <thead style="background-color: #007bff; color: white">
    <tr>
      <th style="padding: 0.5rem; text-align: center">
        <input type="checkbox" id="select-all-recipients" />
      </th>
      <th style="padding: 0.5rem; text-align: center">S/N</th>
      <th style="padding: 0.5rem; text-align: center">Profile Picture</th>
      <th style="padding: 0.5rem; text-align: center">Branch</th>
      <th style="padding: 0.5rem; text-align: left">Name</th>
      <th style="padding: 0.5rem; text-align: left">Email</th>
    </tr>
  </thead>
  <tbody style="border: 1px solid #ddd">
    <tr>
      <td></td>
      <td></td>
      <td
        colspan="6"
        style="
          padding: 1rem;
          text-align: center;
          font-style: italic;
          color: #555;
        "
      >
        Select filters above to view recipients.
      </td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
  </tbody>
</table>

<form
  id="communication-form"
  method="post"
  action="{% url 'send_communication' %}"
  enctype="multipart/form-data"
  style="max-width: 900px"
  data-user-role="{{ request.user.role }}"
>
  {% csrf_token %}

  {% comment %} {% if communication_form.non_field_errors %}
  <div class="alert alert-danger" style="margin-bottom: 1rem;">
    {{ communication_form.non_field_errors }}
  </div>
  {% endif %} {% endcomment %}

  {% if attachment_formset.non_form_errors %}
  <div class="alert alert-danger" style="margin-bottom: 1rem;">
    {{ attachment_formset.non_form_errors }}
  </div>
  {% endif %}

  <div
    style="display: flex; gap: 2rem; align-items: flex-start; flex-wrap: wrap"
  >
    <!-- Left Column: Message Details -->
    <fieldset
      style="
        flex: 1 1 300px;
        border: 1px solid #ccc;
        border-radius: 8px;
        padding: 1rem;
      "
    >
      <legend style="font-weight: 600; font-size: 1.2rem; padding: 0 0.5rem">
        Message Details
      </legend>

      {% for field in communication_form %}
      <div
        class="form-group"
        style="margin-bottom: 1rem; display: flex; flex-direction: column"
      >
        <label
          for="{{ field.id_for_label }}"
          class="form-label"
          style="font-weight: 600; margin-bottom: 0.25rem"
        >
          {{ field.label }}:
        </label>
        {{ field }}
        {% if field.help_text %}
        <small class="form-text text-muted" style="margin-top: 0.25rem">
          {{ field.help_text }}
        </small>
        {% endif %}
        {% if field.errors %}
        <div class="text-danger" style="margin-top: 0.25rem">
          {{ field.errors }}
        </div>
        {% endif %}
      </div>
      {% endfor %}
    </fieldset>

    <!-- Right Column: Attachments -->
    <fieldset
      style="
        flex: 1 1 300px;
        border: 1px solid #ccc;
        border-radius: 8px;
        padding: 1rem;
      "
    >
      <legend style="font-weight: 600; font-size: 1.2rem; padding: 0 0.5rem">
        Attachments
      </legend>
      {{ attachment_formset.management_form }}
      <div id="attachments-container">
        {% for form in attachment_formset.forms %}
        <div
          class="attachment-form {% if forloop.counter > 2 %}extra-attachment{% endif %}"
          style="margin-bottom: 1rem; position: relative"
        >
          {{ form.as_p }}
          {% if forloop.counter > 2 %}
          <button
            type="button"
            class="btn btn-danger remove-attachment"
            style="position: absolute; top: 10px; right: 10px"
          >
            Remove
          </button>
          {% endif %}
        </div>
        {% endfor %}
      </div>
      <button
        type="button"
        id="add-attachment"
        class="btn btn-success"
        style="margin-top: 0.75rem"
      >
        Add More Files
      </button>
    </fieldset>
  </div>

  <input type="hidden" name="selected_recipients" id="selected-recipients" />
  
  <button
    type="submit"
    class="btn btn-primary"
    style="margin-top: 2rem; padding: 0.75rem 2rem; font-size: 1rem"
  >
    Send Message
  </button>
</form>


<!-- jQuery -->
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>

<script>
  $(document).ready(function () {
    const $form = $("#target-group-form");
    const $recipientsTableBody = $("#recipients-table tbody");
    const $selectAll = $("#select-all-recipients");
    const $communicationForm = $("#communication-form");
    const userRole = $communicationForm.data("user-role");

    const fields = {
      branch: $("#id_branch"),
      role: $("#id_role"),
      staffType: $("#id_staff_type"),
      teaching: $("#id_teaching_positions"),
      nonTeaching: $("#id_non_teaching_positions"),
      studentClass: $("#id_student_class"),
      classArm: $("#id_class_arm"),
    };

    let selectedRecipients = new Set();

    // ===== Utility Functions =====

    function areFiltersEmpty() {
      // Check if all filters are empty or unchecked
      for (const key in fields) {
        const field = fields[key];

        // Skip logic for fields not relevant to userRole
        if ((userRole === "student" || userRole === "parent") && key !== "role") continue;
        if ((userRole !== "student" && userRole !== "parent") && key === "role") continue;

        if (field.is(":checkbox")) {
          if (field.prop("checked")) return false;
        } else {
          const val = field.val();
          if (val && val.toString().trim() !== "" && val !== "------------") return false;
        }
      }
      return true;
    }


    function saveFilters() {
      const filters = {};
      $form.find("select, input[type=checkbox]").each(function () {
        const $el = $(this);
        filters[$el.attr("id")] = $el.is(":checkbox") ? $el.prop("checked") : $el.val();
      });
      localStorage.setItem("targetGroupFilters", JSON.stringify(filters));
    }

    function clearFiltersStorage() {
      localStorage.removeItem("targetGroupFilters");
    }

    function clearSelectedRecipients() {
      selectedRecipients.clear();
      localStorage.removeItem("selectedRecipients");
    }

    function loadFilters() {
      const saved = localStorage.getItem("targetGroupFilters");
      if (!saved) return;
      const filters = JSON.parse(saved);
      for (const id in filters) {
        const $el = $("#" + id);
        if ($el.length) {
          if ($el.is(":checkbox")) {
            $el.prop("checked", filters[id]);
          } else {
            $el.val(filters[id]);
          }
        }
      }
    }

    function resetFields(keys) {
      keys.forEach((key) => {
        const field = fields[key];
        if (field.is("select")) {
          field.val("");
        } else {
          field.find("input[type=checkbox]").prop("checked", false);
        }
      });
    }

    function updateBranchVisibility() {
      if (fields.branch.val()) {
        $("#role-field").show();
      } else {
        $("#role-field, #staff-type-field, #teaching-positions-field, #non-teaching-positions-field, #student-class-field, #class-arm-field").hide();
        resetFields(["role", "staffType", "teaching", "nonTeaching", "studentClass", "classArm"]);
      }
    }

    function updateRoleVisibility() {
      const role = fields.role.val();
      if (role === "staff") {
        $("#staff-type-field").show();
        $("#student-class-field, #class-arm-field").hide();
        resetFields(["studentClass", "classArm"]);
        updateStaffTypeVisibility();
      } else if (role === "student") {
        $("#staff-type-field, #teaching-positions-field, #non-teaching-positions-field").hide();
        resetFields(["staffType", "teaching", "nonTeaching"]);
        $("#student-class-field").show();
        updateStudentClassVisibility();
      } else {
        $("#staff-type-field, #teaching-positions-field, #non-teaching-positions-field, #student-class-field, #class-arm-field").hide();
        resetFields(["staffType", "teaching", "nonTeaching", "studentClass", "classArm"]);
      }
    }

    function updateStaffTypeVisibility() {
      const type = fields.staffType.val();
      const $teaching = $("#teaching-positions-field");
      const $nonTeaching = $("#non-teaching-positions-field");

      if (type === "teaching") {
        $teaching.show();
        $nonTeaching.hide().find("input[type=checkbox]").prop("checked", false);
      } else if (type === "non_teaching") {
        $nonTeaching.show();
        $teaching.hide().find("input[type=checkbox]").prop("checked", false);
      } else if (type === "both") {
        $teaching.show();
        $nonTeaching.show();
      } else {
        $teaching.hide().find("input[type=checkbox]").prop("checked", false);
        $nonTeaching.hide().find("input[type=checkbox]").prop("checked", false);
      }
    }

    function updateStudentClassVisibility() {
      const show = !!fields.studentClass.val();
      $("#class-arm-field").toggle(show);
      if (!show) fields.classArm.val("");
    }

    function saveSelectedRecipients() {
      localStorage.setItem("selectedRecipients", JSON.stringify([...selectedRecipients]));
    }

    function loadSelectedRecipients() {
      selectedRecipients = new Set(JSON.parse(localStorage.getItem("selectedRecipients") || "[]"));
    }

    function updateRecipientTableCheckboxStates() {
      $(".recipient-checkbox").each(function () {
        const id = $(this).val();
        $(this).prop("checked", selectedRecipients.has(id));
      });
      $selectAll.prop(
        "checked",
        $(".recipient-checkbox:checked").length === $(".recipient-checkbox").length
      );
    }

    function loadRecipients() {
      // If no filters are applied, always show no users found message
      if (areFiltersEmpty()) {
        recipientsTable.clear().draw();
        $selectAll.prop("checked", false);
        $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">No users found.</td></tr>');
        return;
      }

      // Extra safeguard for student role — avoid sending request if student_class or class_arm is empty
      if (userRole === "student") {
        if (fields.role.val() === "student") {
          const studentClass = fields.studentClass.val();
          const classArm = fields.classArm.val();

          if (!studentClass || !classArm) {
            recipientsTable.clear().draw();
            $selectAll.prop("checked", false);
            $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">Please select class and arm to view students.</td></tr>');
            return;
          }
        }
      }

      const queryData = $form.serializeArray().filter(item => {
      const val = item.value && item.value.trim();
      if (!val) return false;

      const role = fields.role.val();
      const staffType = fields.staffType.val();

      // Skip irrelevant fields
      if (role !== "student" && (item.name === "student_class" || item.name === "class_arm")) return false;
      if (role !== "staff" && item.name === "staff_type") return false;

      // Require at least one teaching/non-teaching checkbox for staff_type 'both'
      if (role === "staff") {
        const hasTeaching = fields.teaching.find("input:checked").length > 0;
        const hasNonTeaching = fields.nonTeaching.find("input:checked").length > 0;

        if (staffType === "both" && !hasTeaching && !hasNonTeaching) {
          recipientsTable.clear().draw();
          $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">Please select at least one Teaching or Non-Teaching position.</td></tr>');
          return false;
        }

        if (staffType === "non_teaching" && !hasNonTeaching) {
          recipientsTable.clear().draw();
          $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">Please select at least one Non-Teaching position.</td></tr>');
          return false;
        }

        if (staffType === "teaching" && !hasTeaching) {
          recipientsTable.clear().draw();
          $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">Please select at least one Teaching position.</td></tr>');
          return false;
        }
      }

      return true;
      });

      if (queryData.length === 0) {
        recipientsTable.clear().draw();
        $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">Please apply valid filters to see results.</td></tr>');
        return;
      }

      // Only make request when queryData is not empty
      $.get("{% url 'get_filtered_users' %}", $.param(queryData), function (response) {
          recipientsTable.clear();
          if (response.length === 0) {
            recipientsTable.draw();
            $selectAll.prop("checked", false);
            $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">No users found.</td></tr>');
            return;
          }

          response.forEach((user, index) => {
            const profilePic = (user.profile_picture && user.profile_picture.url) || "/static/assets/img/profile-pic.png";
            const isChecked = selectedRecipients.has(user.id.toString());

            recipientsTable.row.add([
              `<input type="checkbox" class="recipient-checkbox" value="${user.id}" ${isChecked ? "checked" : ""}>`,
              index + 1,
              `<img src="${profilePic}" alt="Profile Picture" width="30" height="30" style="border-radius: 50%; object-fit: cover;">`,
              user.branch__name,
              `${user.first_name} ${user.last_name}`,
              user.email,
            ]);
          });

          recipientsTable.draw();
          updateRecipientTableCheckboxStates();
        });
      }


    
    
    function handleDependencyChange() {
      clearSelectedRecipients();
      $selectAll.prop("checked", false);
      saveFilters();
      loadRecipients();
    }

    // ===== Event Bindings =====

    fields.branch.on("change", () => {
      updateBranchVisibility();
      updateRoleVisibility();
      handleDependencyChange();
    });

    fields.role.on("change", () => {
      updateRoleVisibility();
      handleDependencyChange();
    });

    fields.staffType.on("change", () => {
      updateStaffTypeVisibility();
      handleDependencyChange();
    });

    fields.studentClass.on("change", () => {
      updateStudentClassVisibility();
      handleDependencyChange();
    });

    $form.find("select, input[type=checkbox]").not("#select-all-recipients").on("change", handleDependencyChange);

    $recipientsTableBody.on("change", ".recipient-checkbox", function () {
      const id = $(this).val();
      if ($(this).is(":checked")) {
        selectedRecipients.add(id);
      } else {
        selectedRecipients.delete(id);
      }
      saveSelectedRecipients();
      updateRecipientTableCheckboxStates();
    });

    $selectAll.on("change", function () {
      const checked = this.checked;
      $(".recipient-checkbox").each(function () {
        $(this).prop("checked", checked);
        const id = $(this).val();
        if (checked) {
          selectedRecipients.add(id);
        } else {
          selectedRecipients.delete(id);
        }
      });
      saveSelectedRecipients();
    });

    $communicationForm.on("submit", function (e) {
      e.preventDefault(); // stop auto submit

      // 1. Validations
      if (["staff", "branch_admin", "superadmin"].includes(userRole) && !fields.branch.val()) {
        alert("Please select a Branch before submitting the form.");
        return false;
      }

      if (["student", "parent"].includes(userRole) && !fields.role.val()) {
        alert("Please select a Role before submitting the form.");
        return false;
      }

      // 2. Inject filters
      $communicationForm.find(".injected-filter-field").remove();
      const filterFieldNames = ["branch", "role", "staff_type", "teaching_positions", "non_teaching_positions", "student_class", "class_arm"];

      filterFieldNames.forEach(function (name) {
        const $fields = $("#target-group-form [name='" + name + "']");

        if ($fields.length && $fields[0].type === "checkbox") {
          // Case: Multiple checkboxes
          $fields.filter(":checked").each(function () {
            $("<input>", {
              type: "hidden",
              name: name,
              value: $(this).val(),
              class: "injected-filter-field"
            }).appendTo($communicationForm);
          });
        } else {
          // Case: dropdowns (single or multiple select), or other fields
          const val = $fields.val();

          if (Array.isArray(val)) {
            // Handle multi-select dropdown (multiple values)
            val.forEach(function (item) {
              $("<input>", {
                type: "hidden",
                name: name,
                value: item,
                class: "injected-filter-field"
              }).appendTo($communicationForm);
            });
          } else if (val !== undefined && val !== null && val !== "") {
            // Single value input
            $("<input>", {
              type: "hidden",
              name: name,
              value: val,
              class: "injected-filter-field"
            }).appendTo($communicationForm);
          }
        }
      });

      // 3. Inject selected recipients
      $communicationForm.find('input[name="selected_recipients"]').remove();

      console.log("Selected Recipients Array:", selectedRecipients);

      [...selectedRecipients].forEach(function (id) {
        $("<input>", {
          type: "hidden",
          name: "selected_recipients",
          value: id
        }).appendTo($communicationForm);
      });

      // 4. Clear local storage filters immediately before submission
      if (typeof clearFiltersStorage === "function") {
        clearFiltersStorage();
      }

      // 4. Submit manually
      $communicationForm.off("submit").submit();

    });

    // ===== Attachments =====

    const maxAttachments = 10;
    let totalForms = parseInt($("#id_attachments-TOTAL_FORMS").val());

    $("#add-attachment").on("click", function () {
      if (totalForms >= maxAttachments) return alert("Maximum attachments reached.");

      const $newForm = $(".attachment-form:first").clone();
      $newForm.find("input, select, textarea").each(function () {
        const name = $(this).attr("name").replace("-0-", `-${totalForms}-`);
        const id = "id_" + name;
        $(this).attr({ name, id }).val("");
        if ($(this).is(":checkbox, :radio")) $(this).prop("checked", false);
      });

      $newForm.find(".remove-attachment").remove();
      $newForm.append('<button type="button" class="btn btn-danger remove-attachment" style="position: absolute; top: 10px; right: 10px;">Remove</button>');
      $("#attachments-container").append($newForm);

      totalForms++;
      $("#id_attachments-TOTAL_FORMS").val(totalForms);
    });

    $("#attachments-container").on("click", ".remove-attachment", function () {
      $(this).closest(".attachment-form").remove();
      totalForms--;
      $("#id_attachments-TOTAL_FORMS").val(totalForms);
    });


    // ===== Initial Load =====

    loadFilters();
    loadSelectedRecipients();
    updateBranchVisibility();
    updateRoleVisibility();
    updateStaffTypeVisibility();
    updateStudentClassVisibility();
    loadRecipients();
  });
</script> 

<script>
  let recipientsTable;

  $(document).ready(function () {
    recipientsTable = $("#recipients-table").DataTable({
      columnDefs: [
        {
          targets: 0,
          orderable: false,
          searchable: false,
        },
      ],
      order: [[1, "asc"]],
    });
  });
  

</script>

{% endblock %}



   
    def get_filtered_recipients(self, target_group_data):
        from accounts.models import TeachingPosition, NonTeachingPosition, StaffProfile, CustomUser
        from django.contrib.contenttypes.models import ContentType
        from django.db.models import Q, QuerySet

        # Extract filters
        role = target_group_data.get('role') or None
        branch = target_group_data.get('branch') or None
        staff_type = target_group_data.get('staff_type') or None
        student_class = target_group_data.get('student_class') or None
        class_arm = target_group_data.get('class_arm') or None
        search = target_group_data.get('search')

        def ensure_position_objects(position_ids, model_cls):
            if position_ids and isinstance(position_ids[0], (str, int)):
                return list(model_cls.objects.filter(id__in=position_ids))
            return position_ids or []

        teaching_positions = ensure_position_objects(target_group_data.get('teaching_positions', []), TeachingPosition)
        non_teaching_positions = ensure_position_objects(target_group_data.get('non_teaching_positions', []), NonTeachingPosition)

        qs = CustomUser.objects.filter(is_active=True).exclude(id=self.user.id)

        def filter_staff(
            qs,
            role,
            staff_type,
            teaching_positions=None,
            non_teaching_positions=None,
            student_class=None,
            class_arm=None,
            request_user=None,
            role_scope=None,
            branch=None
        ):
            if not role:
                return qs.none()

            qs = qs.filter(role=role)

            if branch:
                qs = qs.filter(branch=branch)

            def apply_position_filter(base_qs, staff_type, positions, positions_field):
                staff_qs = base_qs.filter(staff_type=staff_type)

                if not positions:
                    return staff_qs

                positions = [p for p in positions if p]
                if not positions:
                    return staff_qs

                content_type = ContentType.objects.get_for_model(positions[0].__class__)

                # Direct filter
                direct_ids = staff_qs.filter(**{positions_field: positions}).values_list('id', flat=True)

                # Via profile
                via_profile_ids = StaffProfile.objects.filter(
                    position_content_type=content_type,
                    position_object_id__in=[p.id for p in positions],
                    user__role__in=role_scope,
                    user__staff_type=staff_type
                ).values_list('user_id', flat=True)

                all_ids = set(direct_ids) | set(via_profile_ids)
                staff_qs = staff_qs.filter(id__in=all_ids)

                # Special class teacher filter
                is_class_teacher = any(getattr(p, 'is_class_teacher', False) for p in positions)
                if is_class_teacher:
                    if not student_class or not class_arm:
                        return base_qs.none()

                    teaching_ct = ContentType.objects.get_for_model(TeachingPosition)
                    managed_ids = StaffProfile.objects.filter(
                        position_content_type=teaching_ct,
                        position_object_id__in=TeachingPosition.objects.filter(is_class_teacher=True).values_list('id', flat=True),
                        managing_class_id=getattr(student_class, 'id', student_class),
                        managing_class_arm_id=getattr(class_arm, 'id', class_arm)
                    ).values_list('user_id', flat=True)

                    staff_qs = staff_qs.filter(id__in=managed_ids)

                return staff_qs

            if staff_type == 'teaching':
                return apply_position_filter(qs, 'teaching', teaching_positions, 'teaching_positions__in')
            elif staff_type == 'non_teaching':
                return apply_position_filter(qs, 'non_teaching', non_teaching_positions, 'non_teaching_positions__in')
            elif staff_type == 'both':
                teaching_qs = apply_position_filter(qs, 'teaching', teaching_positions, 'teaching_positions__in')
                non_teaching_qs = apply_position_filter(qs, 'non_teaching', non_teaching_positions, 'non_teaching_positions__in')
                return (teaching_qs | non_teaching_qs).distinct()
            else:
                return qs.filter(staff_type=staff_type)

        user_role = self.user.role
        VALID_ROLES = {
            "student": ['staff', 'branch_admin'],
            "parent": ['staff', 'branch_admin'],
            "default": ['staff', 'branch_admin', 'superadmin']
        }

        # Apply branch restriction
        if user_role in ['student', 'parent', 'staff', 'branch_admin'] and self.user.branch:
            qs = qs.filter(branch=self.user.branch)

        if user_role == 'student':
            if not role:
                return qs.none()

            if role == 'student':
                if not student_class:
                    return qs.none()
                qs = qs.filter(role='student', studentprofile__current_class_id=student_class)
                if class_arm:
                    qs = qs.filter(studentprofile__current_class_arm_id=class_arm)
                return qs

            elif role == 'parent':
                try:
                    parent_user_id = self.user.studentprofile.parent.user.id
                    return qs.filter(id=parent_user_id, role='parent')
                except Exception:
                    return qs.none()

            elif role == 'staff':
                return filter_staff(
                    qs=qs,
                    role=role,
                    staff_type=staff_type,
                    teaching_positions=teaching_positions,
                    non_teaching_positions=non_teaching_positions,
                    student_class=student_class,
                    class_arm=class_arm,
                    request_user=self.user,
                    role_scope=VALID_ROLES['student'],
                    branch=self.user.branch
                )

        elif user_role == 'parent':
            if staff_type != 'teaching' or not teaching_positions:
                return qs.none()

            has_class_teacher = any(getattr(p, 'is_class_teacher', False) for p in teaching_positions)
            if not has_class_teacher or not student_class or not class_arm:
                return qs.none()

            return filter_staff(
                qs=qs,
                role='staff',
                staff_type='teaching',
                teaching_positions=teaching_positions,
                student_class=student_class,
                class_arm=class_arm,
                request_user=self.user,
                role_scope=VALID_ROLES['parent'],
                branch=self.user.branch
            )

        elif user_role in ['staff', 'branch_admin', 'superadmin']:
            if not branch:
                return qs.none()

            qs = qs.filter(branch=branch)

            if role and staff_type:
                return filter_staff(
                    qs=qs,
                    role=role,
                    staff_type=staff_type,
                    teaching_positions=teaching_positions,
                    non_teaching_positions=non_teaching_positions,
                    student_class=student_class,
                    class_arm=class_arm,
                    request_user=self.user,
                    role_scope=VALID_ROLES['default'],
                    branch=branch
                )
            elif role:
                qs = qs.filter(role=role)

        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )

        return qs.distinct()





@method_decorator([login_required, require_POST], name='dispatch')
class SendCommunicationView(View):

    def flatten_querydict(self, qd: QueryDict):
        return {k: v[0] if len(v) == 1 else v for k, v in qd.lists()}

    def _get_allowed_recipients(self, target_group_form, user):
        recipients = target_group_form.get_filtered_recipients(target_group_form.cleaned_data)
        return recipients.exclude(id=user.id)

    def _get_selected_recipients(self, request, allowed_recipients):
        selected_ids = request.POST.getlist('selected_recipients')
        return allowed_recipients.filter(id__in=selected_ids)

    def _parse_manual_emails(self, email_string):
        emails = [email.strip() for email in email_string.split(',') if email.strip()]
        valid_emails = []
        for email in emails:
            try:
                validate_email(email)
                valid_emails.append(email.lower())
            except ValidationError:
                messages.warning(self.request, f"Invalid manual email skipped: {email}")
        return valid_emails

    def _check_for_duplicate_emails(self, selected_recipients, manual_emails, form):
        if selected_recipients.exists():
            selected_emails = set(email.lower() for email in selected_recipients.values_list('email', flat=True))
            duplicates = selected_emails.intersection(set(manual_emails))
            if duplicates:
                form.add_error(None, f"Duplicate manual email(s): {', '.join(duplicates)}")
                return False
        return True

    def _render_with_errors(self, communication_form, target_group_form, attachment_formset):
        def flatten_querydict(qd):
            return {k: qd.getlist(k) if len(qd.getlist(k)) > 1 else qd.get(k) for k in qd}

        post_data = flatten_querydict(self.request.POST)

        self.request.session['communication_form_data'] = {
            k: v for k, v in post_data.items() if k in communication_form.fields
        }
        self.request.session['target_group_form_data'] = {
            k: v for k, v in post_data.items() if k in target_group_form.fields
        }
        self.request.session['attachment_formset_data'] = post_data
        self.request.session['non_field_errors'] = list(communication_form.non_field_errors())
        self.request.session['form_error'] = True

        messages.error(self.request, "There was an error with your submission. Please correct the highlighted fields.")
        return redirect('communication_index')

    def post(self, request):
        self.request = request

        communication_form = CommunicationForm(request.POST, user=request.user)
        attachment_formset = AttachmentFormSet(request.POST, request.FILES)

        # Sanitize and ensure only valid numeric IDs are passed
        def clean_id_list(raw_list):
            clean = []
            for item in raw_list:
                try:
                    clean.append(str(int(item.strip())))
                except (ValueError, TypeError):
                    continue
            return clean

        saved_filter_data = {
            'branch': request.user.branch.id if request.user.role in ['student', 'parent'] else request.POST.get('saved_branch', ''),
            'role': request.POST.get('saved_role', ''),
            'staff_type': request.POST.get('saved_staff_type', ''),
            'student_class': request.POST.get('saved_student_class', ''),
            'class_arm': request.POST.get('saved_class_arm', ''),
            'teaching_positions': clean_id_list(request.POST.get('saved_teaching_positions', '').split(',')),
            'non_teaching_positions': clean_id_list(request.POST.get('saved_non_teaching_positions', '').split(',')),
        }

        from django.http import QueryDict
        form_data = QueryDict('', mutable=True)
        for key in ['branch', 'role', 'staff_type', 'student_class', 'class_arm']:
            form_data[key] = saved_filter_data[key]
        form_data.setlist('teaching_positions', saved_filter_data['teaching_positions'])
        form_data.setlist('non_teaching_positions', saved_filter_data['non_teaching_positions'])

        target_group_form = CommunicationTargetGroupForm(data=form_data, user=request.user)
        if not target_group_form.is_valid():
            communication_form.add_error(None, "Invalid target group filters.")
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        if not communication_form.is_valid() or not attachment_formset.is_valid():
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        try:
            validate_attachment_formset(attachment_formset)
        except ValidationError as e:
            messages.error(request, str(e))
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        allowed_recipients = self._get_allowed_recipients(target_group_form, request.user)
        selected_recipients = self._get_selected_recipients(request, allowed_recipients)

        manual_emails_raw = communication_form.cleaned_data.get('manual_emails', '')
        valid_manual_emails = self._parse_manual_emails(manual_emails_raw)

        if not selected_recipients.exists() and not valid_manual_emails:
            error_msg = "Please select at least one recipient."
            if request.user.role not in ['student', 'parent']:
                error_msg += " Or provide a valid manual email."
            communication_form.add_error(None, error_msg)
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        if not self._check_for_duplicate_emails(selected_recipients, valid_manual_emails, communication_form):
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        communication = communication_form.save(commit=False)
        communication.sender = request.user
        communication.requires_response = communication_form.cleaned_data.get('requires_response', False)
        communication.sent = False
        communication.is_draft = communication_form.cleaned_data.get('is_draft', False)
        communication.selected_recipient_ids = list(selected_recipients.values_list('id', flat=True))
        communication.manual_emails = valid_manual_emails
        communication.saved_filter_data = {
            f"id_{k}": v for k, v in saved_filter_data.items()
        }
        communication.save()

        for form in attachment_formset:
            if form.cleaned_data.get('file'):
                form.instance.communication = communication
                form.save()

        if not communication.is_draft and communication.is_due():
            send_communication_to_recipients(
                communication=communication,
                selected_recipients=selected_recipients,
                manual_emails=valid_manual_emails
            )
            communication.sent = True
            communication.sent_at = timezone.now()
            communication.save()
            messages.success(request, "Communication sent successfully.")
            return redirect('communication_success')

        elif communication.is_draft:
            messages.success(request, "Communication saved as draft.")
            return redirect('draft_messages')

        else:
            url = reverse('communication_scheduled')
            query_string = urlencode({
                'scheduled_time': communication.scheduled_time.strftime('%Y-%m-%d %I:%M:%S %p'),
                'sent': 'false'
            })
            messages.success(request, f"Scheduled for {communication.scheduled_time.strftime('%b %d, %Y at %I:%M %p')}.")
            return redirect(f"{url}?{query_string}")

@method_decorator([login_required, require_http_methods(["GET", "POST"])], name='dispatch')
class EditDraftMessageView(View):

    def _clean_id_list(self, raw_list):
        cleaned = []
        for item in raw_list:
            try:
                cleaned.append(str(int(item.strip())))
            except (ValueError, TypeError):
                continue
        return cleaned

    def _render_with_errors(self, communication_form, target_group_form, attachment_formset):
        messages.error(self.request, "There was an error with your submission. Please correct the highlighted fields.")
        return render(self.request, 'communications/edit_draft.html', {
            'communication_form': communication_form,
            'target_group_form': target_group_form,
            'attachment_formset': attachment_formset,
            'editing_draft': True,
            'communication': self.draft,
            'user_role': self.request.user.role,
            'user_branch_id': self.request.user.branch.id if hasattr(self.request.user, 'branch') else '',
        })

    def get(self, request, pk):
        draft = get_object_or_404(Communication, pk=pk, sender=request.user, is_draft=True, sent=False)
        self.draft = draft

        saved_filter_data = draft.saved_filter_data or {}
        selected_recipient_ids = draft.selected_recipient_ids or []

        initial_data = {
            'branch': Branch.objects.filter(id=saved_filter_data.get('id_branch')).first() if saved_filter_data.get('id_branch') else None,
            'role': saved_filter_data.get('id_role', ''),
            'staff_type': saved_filter_data.get('id_staff_type', ''),
            'student_class': StudentClass.objects.filter(id=saved_filter_data.get('id_student_class')).first() if saved_filter_data.get('id_student_class') else None,
            'class_arm': ClassArm.objects.filter(id=saved_filter_data.get('id_class_arm')).first() if saved_filter_data.get('id_class_arm') else None,
            'teaching_positions': TeachingPosition.objects.filter(
                id__in=self._clean_id_list(saved_filter_data.get('id_teaching_positions', []))
            ),
            'non_teaching_positions': NonTeachingPosition.objects.filter(
                id__in=self._clean_id_list(saved_filter_data.get('id_non_teaching_positions', []))
            ),
        }

        target_group_form = CommunicationTargetGroupForm(initial=initial_data, user=request.user)

        dummy_data = QueryDict('', mutable=True)
        for key in ['id_branch', 'id_role', 'id_staff_type', 'id_student_class', 'id_class_arm']:
            dummy_data[key] = saved_filter_data.get(key, '')
        dummy_data.setlist('id_teaching_positions', self._clean_id_list(saved_filter_data.get('id_teaching_positions', [])))
        dummy_data.setlist('id_non_teaching_positions', self._clean_id_list(saved_filter_data.get('id_non_teaching_positions', [])))

        dummy_form = CommunicationTargetGroupForm(data=dummy_data, user=request.user)
        if dummy_form.is_valid():
            allowed_recipients = dummy_form.get_filtered_recipients(dummy_form.cleaned_data).exclude(id=request.user.id)
        else:
            allowed_recipients = CustomUser.objects.filter(id__in=selected_recipient_ids)

        selected_recipients = allowed_recipients.filter(id__in=selected_recipient_ids)

        communication_form = CommunicationForm(instance=draft, user=request.user)
        attachment_formset = AttachmentFormSet(instance=draft, prefix="attachments")

        context = {
            'communication_form': communication_form,
            'target_group_form': target_group_form,
            'attachment_formset': attachment_formset,
            'communication': draft,
            'saved_filter_data': json.dumps(saved_filter_data),
            'selected_recipient_ids': json.dumps(selected_recipient_ids),
            'recipients': allowed_recipients,
            'selected_recipients': selected_recipients,
            'editing_draft': True,
            'user_branch_id': request.user.branch.id if getattr(request.user, 'branch', None) else '',
            'user_role': request.user.role,
        }

        return render(request, 'communications/edit_draft.html', context)

    def post(self, request, pk):
        self.request = request
        draft = get_object_or_404(Communication, pk=pk, sender=request.user, is_draft=True, sent=False)
        self.draft = draft

        communication_form = CommunicationForm(request.POST, request.FILES, instance=draft, user=request.user)
        attachment_formset = AttachmentFormSet(request.POST, request.FILES, instance=draft)

        saved_filter_data = {
            'branch': request.user.branch.id if request.user.role in ['student', 'parent'] else request.POST.get('saved_branch', ''),
            'role': request.POST.get('saved_role', ''),
            'staff_type': request.POST.get('saved_staff_type', ''),
            'student_class': request.POST.get('saved_student_class', ''),
            'class_arm': request.POST.get('saved_class_arm', ''),
            'teaching_positions': self._clean_id_list(request.POST.get('saved_teaching_positions', '').split(',')),
            'non_teaching_positions': self._clean_id_list(request.POST.get('saved_non_teaching_positions', '').split(',')),
        }

        form_data = QueryDict('', mutable=True)
        for key in ['branch', 'role', 'staff_type', 'student_class', 'class_arm']:
            form_data[key] = saved_filter_data[key]
        form_data.setlist('teaching_positions', saved_filter_data['teaching_positions'])
        form_data.setlist('non_teaching_positions', saved_filter_data['non_teaching_positions'])

        target_group_form = CommunicationTargetGroupForm(data=form_data, user=request.user)

        if not (communication_form.is_valid() and target_group_form.is_valid() and attachment_formset.is_valid()):
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        try:
            validate_attachment_formset(attachment_formset)
        except ValidationError as e:
            messages.error(request, str(e))
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        branch = request.user.branch if request.user.role in ['student', 'parent'] else target_group_form.cleaned_data.get('branch')
        if not branch:
            target_group_form.add_error('branch', "Please select a Branch.")
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        allowed_recipients = target_group_form.get_filtered_recipients(target_group_form.cleaned_data).exclude(id=request.user.id)
        selected_recipients = allowed_recipients.filter(id__in=request.POST.getlist('selected_recipients'))

        manual_emails_raw = communication_form.cleaned_data.get('manual_emails', '')
        valid_manual_emails = self._parse_manual_emails(manual_emails_raw)

        if not selected_recipients.exists() and not valid_manual_emails:
            communication_form.add_error(None, "Please select at least one recipient or enter a valid manual email.")
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        if not self._check_for_duplicate_emails(selected_recipients, valid_manual_emails, communication_form):
            return self._render_with_errors(communication_form, target_group_form, attachment_formset)

        communication = communication_form.save(commit=False)
        communication.requires_response = communication_form.cleaned_data.get('requires_response', False)
        communication.sent = False
        communication.is_draft = communication_form.cleaned_data.get('is_draft', False)
        communication.selected_recipient_ids = list(selected_recipients.values_list('id', flat=True))
        communication.manual_emails = valid_manual_emails
        communication.saved_filter_data = {
            'id_branch': str(branch.id) if branch else '',
            'id_role': target_group_form.cleaned_data.get('role', ''),
            'id_staff_type': target_group_form.cleaned_data.get('staff_type', ''),
            'id_student_class': str(target_group_form.cleaned_data['student_class'].id) if target_group_form.cleaned_data.get('student_class') else '',
            'id_class_arm': str(target_group_form.cleaned_data['class_arm'].id) if target_group_form.cleaned_data.get('class_arm') else '',
            'id_teaching_positions': [str(pos.id) for pos in target_group_form.cleaned_data.get('teaching_positions', [])],
            'id_non_teaching_positions': [str(pos.id) for pos in target_group_form.cleaned_data.get('non_teaching_positions', [])],
        }
        communication.save()

        for form in attachment_formset:
            if form.cleaned_data.get('file'):
                form.instance.communication = communication
                form.save()

        if not communication.is_draft and communication.is_due():
            send_communication_to_recipients(
                communication=communication,
                selected_recipients=selected_recipients,
                manual_emails=valid_manual_emails
            )
            communication.sent = True
            communication.sent_at = timezone.now()
            communication.save()
            messages.success(request, "Communication sent successfully.")
            return redirect('communication_success')

        elif communication.is_draft:
            messages.success(request, "Draft updated successfully.")
            return redirect('draft_messages')

        else:
            url = reverse('communication_scheduled')
            query_string = urlencode({
                'scheduled_time': communication.scheduled_time.strftime('%Y-%m-%d %I:%M:%S %p'),
                'sent': 'false'
            })
            messages.success(request, f"Scheduled for {communication.scheduled_time.strftime('%b %d, %Y at %I:%M %p')}.")
            return redirect(f"{url}?{query_string}")
