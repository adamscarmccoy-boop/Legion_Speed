import os

skills_dir = r"C:\Users\adams\.gemini\config\skills"
skills = [
    "AUDIO-book-skill",
    "audiobook-cpp-bridge-skill",
    "codebase-navigator-skill",
    "sovereign-orchestration-skill"
]

for skill in skills:
    skill_path = os.path.join(skills_dir, skill)
    if not os.path.exists(skill_path):
        continue
        
    md_file = None
    for f in os.listdir(skill_path):
        if f.endswith(".md"):
            md_file = os.path.join(skill_path, f)
            break
            
    if md_file:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        if not content.startswith("---"):
            yaml = f"---\nname: {skill}\ndescription: Global skill extracted from .genkit for Sovereign Audio Intelligence.\n---\n\n"
            content = yaml + content
            
            # Save as SKILL.md
            new_path = os.path.join(skill_path, "SKILL.md")
            with open(new_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            # If the original file wasn't SKILL.md, remove it
            if md_file != new_path:
                os.remove(md_file)
            print(f"Fixed {skill}")
