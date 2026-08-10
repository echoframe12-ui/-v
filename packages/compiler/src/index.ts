import { Opcode, Instruction, IRProgram } from '@omega-v/ir';

/**
 * Oceanicum Compiler: Compiles human-readable rule definitions into Oceanicum IR programs
 */
export class RuleCompiler {
  /**
   * Compile a rule definition string into an IRProgram
   *
   * Supported patterns:
   *  - `responseTime < 100`
   *  - `statusCode == 200`
   *  - `responseTime < 100 && statusCode == 200`
   *  - `status == "ok"`
   */
  public compile(ruleName: string, ruleDefinition: string, version: string = '1.0.0'): IRProgram {
    const instructions: Instruction[] = [];
    const tokens = ruleDefinition.split(/\s+(&&|\|\|)\s+/);

    let pendingLogicalOp: Opcode | null = null;

    for (let i = 0; i < tokens.length; i++) {
      const token = tokens[i].trim();

      if (token === '&&') {
        pendingLogicalOp = Opcode.AND;
        continue;
      }
      if (token === '||') {
        pendingLogicalOp = Opcode.OR;
        continue;
      }

      // Parse simple binary expression: `left op right`
      const match = token.match(/^([a-zA-Z0-9_.]+)\s*(==|!=|<=|>=|<|>)\s*(.+)$/);
      if (!match) {
        throw new Error(`Compiler Syntax Error: Unable to parse expression '${token}' in rule '${ruleName}'`);
      }

      const [, field, operator, rawVal] = match;
      const parsedVal = this.parseValue(rawVal);
      const fullPath = field.startsWith('metadata.') ? field : `metadata.${field}`;

      instructions.push({ opcode: Opcode.LOAD, operand: fullPath });
      instructions.push({ opcode: Opcode.CONST, operand: parsedVal });

      switch (operator) {
        case '==':
          instructions.push({ opcode: Opcode.EQ });
          break;
        case '!=':
          instructions.push({ opcode: Opcode.NEQ });
          break;
        case '<':
          instructions.push({ opcode: Opcode.LT });
          break;
        case '<=':
          instructions.push({ opcode: Opcode.LTE });
          break;
        case '>':
          instructions.push({ opcode: Opcode.GT });
          break;
        case '>=':
          instructions.push({ opcode: Opcode.GTE });
          break;
      }

      if (pendingLogicalOp) {
        instructions.push({ opcode: pendingLogicalOp });
        pendingLogicalOp = null;
      }
    }

    instructions.push({
      opcode: Opcode.ASSERT,
      operand: `Rule '${ruleName}' constraint verified: ${ruleDefinition}`,
    });

    return {
      name: ruleName,
      version,
      instructions,
    };
  }

  private parseValue(val: string): unknown {
    val = val.trim();
    if (val === 'true') return true;
    if (val === 'false') return false;
    if (val === 'null') return null;
    if (!isNaN(Number(val))) return Number(val);
    // Remove surrounding quotes if string
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      return val.slice(1, -1);
    }
    return val;
  }
}

export default RuleCompiler;
