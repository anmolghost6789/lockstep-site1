import { requireUser } from '@/lib/registry/auth';
import { RegisterForm } from '@/components/registry/client';
import { SectionLabel } from '@/components/site/section-label';
import { h1 } from '@/components/registry/ui';

export default async function NewSkillPage() {
  await requireUser('publisher');
  return (
    <div className="max-w-[880px]">
      <div className="flex flex-col gap-3">
        <SectionLabel>Register</SectionLabel>
        <h1 className={h1}>Add a pack, a skill, or a new version</h1>
        <p className="max-w-[640px] font-inter text-[14px] font-medium leading-[20px] text-[#646464] dark:text-neutral-400">
          A skill is a folder with a SKILL.md whose frontmatter has a name and a description (the open Agent Skills format). A pack is a
          whole package, such as a Claude Code project with skills in .claude/skills/, plus its subagents, hooks, config, templates and docs.
          Spreadsheets and images are kept as files. Submitting an existing name adds a new version.
        </p>
      </div>
      <div className="mt-8">
        <RegisterForm />
      </div>
    </div>
  );
}
