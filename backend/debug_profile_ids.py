import re

with open('frontend/profile.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find all getElementById calls
pat = re.compile(r"getElementById\(['\"]([^'\"]+)['\"]\)")
ids_in_js = set(pat.findall(content))

# Find all id= attributes in HTML
pat2 = re.compile(r'\bid=["\']([^"\']+)["\']')
ids_in_html = set(pat2.findall(content))

print("=== IDs referenced in JS but NOT in HTML ===")
missing = ids_in_js - ids_in_html
for m in sorted(missing):
    print(f"  MISSING: #{m}")

print()
print("=== IDs in HTML (form fields) ===")
for i in sorted(ids_in_html):
    if i not in ('view-mode','edit-mode','student-view','employer-view','admin-view',
                 'student-edit','employer-edit','admin-edit','edit-mode','avatar-circle',
                 'avatar-img','photo-controls','photo-hint-view','btn-remove-photo',
                 'avatar-file-input','display-name','display-email','display-phone',
                 'display-verified','display-role-badge','btn-edit-profile',
                 'skills-pill-box','new-skill-input','save-btn','v-degree',
                 'v-specialization','v-college','v-grad-year','v-fresher','v-job-type',
                 'v-address','v-bio','v-roles','v-skills','v-company','v-biz-type',
                 'v-website','v-emp-address','v-description'):
        print(f"  {i}")
